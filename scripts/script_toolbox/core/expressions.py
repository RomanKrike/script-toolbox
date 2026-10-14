# -*- coding: utf-8 -*-
"""Side-effect-free expression language shared by all hosts (Python 2.7)."""
from __future__ import print_function
import json
import operator
import re
from ..pycompat import text_type, integer_type

RESERVED_WORDS = frozenset(('if', 'then', 'else', 'true', 'false'))
NAME_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
TOKEN_PATTERN = re.compile(r'\s+|"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*|==|!=|>=|<=|&&|\|\||[!<>()]')
PROPERTIES = ('visible', 'enabled')

class ExpressionError(ValueError):
    def __init__(self, message, position=0):
        self.reason, self.position = text_type(message), position
        ValueError.__init__(self, '{0} (column {1})'.format(message, position + 1))

def validate_name(name):
    name = text_type(name or '')
    if not NAME_PATTERN.match(name):
        raise ValueError('Use letters A-Z, digits and _. Start with a letter or _.')
    if name.lower() in RESERVED_WORDS:
        raise ValueError('{0!r} is a reserved expression word.'.format(name))
    return name

def tokenize(source):
    source = text_type(source or '')
    if len(source) > 4096:
        raise ExpressionError('Expression exceeds 4096 characters')
    result, position = [], 0
    while position < len(source):
        match = TOKEN_PATTERN.match(source, position)
        if match is None:
            raise ExpressionError('Unexpected character', position)
        if not match.group().isspace():
            result.append((match.group(), position, match.end()))
        position = match.end()
    if len(result) > 256:
        raise ExpressionError('Expression exceeds 256 tokens')
    return result

class Expression(object):
    def __init__(self, source):
        self.source = text_type(source or '')
        self.tokens, self.index, self.dependencies = tokenize(self.source), 0, set()
        self.tree = self._conditional()
        if self.index != len(self.tokens):
            self._error('Unexpected token')
    def _peek(self):
        return self.tokens[self.index][0] if self.index < len(self.tokens) else None
    def _error(self, message):
        position = self.tokens[self.index][1] if self.index < len(self.tokens) else len(self.source)
        raise ExpressionError(message, position)
    def _take(self, expected=None):
        value = self._peek()
        if value is None or (expected is not None and value != expected):
            self._error('Expected {0}'.format(expected or 'a value'))
        self.index += 1
        return value
    def _conditional(self):
        if self._peek() == 'if':
            self._take('if')
            condition = self._or()
            self._take('then')
            yes = self._conditional()
            self._take('else')
            return ('if', condition, yes, self._conditional())
        return self._or()
    def _or(self):
        return self._binary(self._and, ('||',))
    def _and(self):
        return self._binary(self._comparison, ('&&',))
    def _binary(self, read, ops):
        value = read()
        while self._peek() in ops:
            op = self._take()
            value = (op, value, read())
        return value
    def _comparison(self):
        value = self._unary()
        if self._peek() in ('==', '!=', '>', '<', '>=', '<='):
            op = self._take()
            value = (op, value, self._unary())
        return value
    def _unary(self):
        if self._peek() == '!':
            self._take()
            return ('!', self._unary())
        if self._peek() == '(':
            self._take()
            value = self._conditional()
            self._take(')')
            return value
        value = self._take()
        if value in ('true', 'false'):
            return ('literal', value == 'true')
        if value.startswith('"'):
            try:
                return ('literal', json.loads(value))
            except ValueError:
                raise ExpressionError('Invalid string escape', self.tokens[self.index - 1][1])
        if re.match(r'^-?\d', value):
            return ('literal', float(value) if '.' in value else int(value))
        if NAME_PATTERN.match(value) and value.lower() not in RESERVED_WORDS:
            self.dependencies.add(value)
            return ('reference', value)
        self._error('Expected a literal or parameter name')
    def evaluate(self, resolve, boolean=False):
        def require_bool(value):
            if not isinstance(value, bool):
                raise ExpressionError('Expected true or false')
            return value
        def category(value):
            if isinstance(value, bool): return 'bool'
            if isinstance(value, (int, integer_type, float)): return 'number'
            if isinstance(value, text_type): return 'string'
            raise ExpressionError('Only scalar bool, number and string parameters are supported')
        def visit(node):
            op = node[0]
            if op == 'literal': return node[1]
            if op == 'reference':
                value = resolve(node[1])
                category(value)
                return value
            if op == '!': return not require_bool(visit(node[1]))
            if op == 'if': return visit(node[2] if require_bool(visit(node[1])) else node[3])
            a = visit(node[1])
            if op == '&&': return require_bool(a) and require_bool(visit(node[2]))
            if op == '||': return require_bool(a) or require_bool(visit(node[2]))
            b = visit(node[2])
            if category(a) != category(b): raise ExpressionError('Comparison types do not match')
            if op not in ('==', '!=') and category(a) == 'bool':
                raise ExpressionError('Boolean values support only == and !=')
            return {'==': operator.eq, '!=': operator.ne, '>': operator.gt,
                    '<': operator.lt, '>=': operator.ge, '<=': operator.le}[op](a, b)
        result = visit(self.tree)
        return require_bool(result) if boolean else result

def rewrite_expression(source, replacements):
    """Token rewrite: never replace strings or a substring of another name."""
    try: tokens = tokenize(source)
    except ExpressionError: return source
    for value, start, end in reversed(tokens):
        if NAME_PATTERN.match(value) and value.lower() not in RESERVED_WORDS and value in replacements:
            source = source[:start] + replacements[value] + source[end:]
    return source

class ExpressionState(object):
    """Compiled dependency index; conditions read values, never other UI states."""
    def __init__(self, document):
        from ..model.items import walk_items
        self.items = dict((item['id'], item) for item in walk_items(document, include_sections=True))
        self.names = {}
        for item in self.items.values(): self.names.setdefault(item['name'], []).append(item)
        self.compiled, self.dependents, self.errors = {}, {}, {}
        for item in self.items.values():
            ui = item.get('ui', {})
            for prop in PROPERTIES:
                if not ui.get(prop + '_expression_enabled', False): continue
                key = (item['id'], prop)
                try:
                    expr = Expression(ui.get(prop + '_expression', ''))
                    bindings, refs = ui.get(prop + '_references', {}), {}
                    for name in expr.dependencies:
                        target = self.items.get(bindings[name]) if name in bindings else self._named(name)
                        if target is None: raise ExpressionError('Missing parameter: ' + name)
                        refs[name] = target['id']
                        self.dependents.setdefault(target['id'], set()).add(item['id'])
                    self.compiled[key] = (expr, refs)
                except (ExpressionError, ValueError) as exc: self.errors[key] = text_type(exc)
    def _named(self, name):
        candidates = self.names.get(name, [])
        if len(candidates) != 1:
            raise ExpressionError(('Ambiguous' if candidates else 'Unknown') + ' parameter: ' + name)
        return candidates[0]
    def evaluate(self, item_id, prop):
        key, item = (item_id, prop), self.items[item_id]
        fallback = bool(item.get('ui', {}).get(prop, True))
        entry = self.compiled.get(key)
        if entry is None: return fallback
        expr, refs = entry
        def resolve(name):
            target = self.items[refs[name]]
            from ..model.item_registry import ITEM_TYPES
            definition = ITEM_TYPES.get(target['kind'])
            if definition is None or not definition.has_capability('has_value'):
                raise ExpressionError('Parameter has no value: ' + name)
            if definition.has_capability('state_toggle') and target.get('props', {}).get('state_source') == 'script':
                raise ExpressionError('Script-driven state is not an expression value: ' + name)
            return target.get('props', {}).get('value')
        try:
            value = expr.evaluate(resolve, boolean=True)
            self.errors.pop(key, None)
            return value
        except ExpressionError as exc:
            self.errors[key] = text_type(exc)
            return fallback

def bind_expression_references(document):
    """Persist ID bindings for known names without rebinding deleted targets."""
    from ..model.items import walk_items
    items = list(walk_items(document, include_sections=True))
    names = {}
    for item in items: names.setdefault(item['name'], []).append(item['id'])
    for item in items:
        ui = item['ui']
        for prop in PROPERTIES:
            source = ui.get(prop + '_expression', '')
            if not source: continue
            try: expr = Expression(source)
            except ExpressionError: continue
            old, refs = ui.get(prop + '_references', {}), {}
            for name in expr.dependencies:
                if name in old: refs[name] = old[name]
                elif len(names.get(name, [])) == 1: refs[name] = names[name][0]
            ui[prop + '_references'] = refs
