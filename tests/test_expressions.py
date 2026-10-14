import pytest
from script_toolbox.core.expressions import (Expression, ExpressionError, ExpressionState,
    bind_expression_references, validate_name, rewrite_expression)
from script_toolbox.core.editor_document import EditorDocumentController
from script_toolbox.model.items import create_item, normalize_document


def document():
    checkbox = create_item('checkbox', {'name': 'use_preview', 'props': {'value': True}})
    button = create_item('button', {'name': 'capture', 'ui': {
        'visible_expression_enabled': True, 'visible_expression': 'use_preview'}})
    folder = create_item('folder', {'name': 'tools', 'items': [checkbox, button]})
    doc = normalize_document({'sections': [folder]})
    return doc, doc['sections'][0]['items']

@pytest.mark.parametrize('source,value', [
    ('true', True), ('!false', True), ('1 < 2 && 3 >= 3', True),
    ('false || true && false', False), ('(false || true) && true', True),
    ('mode == "preview"', True), ('if use_preview then 1000 else 1920', 1000),
    ('if false then missing else "ok"', 'ok'), ('-2 < 0.5', True),
    ('if true then if false then false else true else false', True),
])
def test_language(source, value):
    values = {'mode': 'preview', 'use_preview': True}
    assert Expression(source).evaluate(values.__getitem__) == value

@pytest.mark.parametrize('source', ['__import__("os")', 'mode.value', '{mode}', 'a[0]',
                                     'true ==', '"bad\\x"', '1 < 2 < 3', 'True', ''])
def test_language_rejects_python_and_malformed_input(source):
    with pytest.raises(ExpressionError): Expression(source)

@pytest.mark.parametrize('source', ['1', '"true"', '1 == true', '!1', 'true > false'])
def test_boolean_conditions_do_not_coerce(source):
    with pytest.raises(ExpressionError): Expression(source).evaluate(lambda _: None, boolean=True)

@pytest.mark.parametrize('name', ['if', 'IF', 'True', 'else', 'false', 'a b', '1abc', ''])
def test_names(name):
    with pytest.raises(ValueError): validate_name(name)


def test_dependencies_fallback_and_id_binding():
    doc, (checkbox, button) = document()
    state = ExpressionState(doc)
    assert state.dependents[checkbox['id']] == {button['id']}
    assert state.evaluate(button['id'], 'visible') is True
    checkbox['props']['value'] = False
    assert state.evaluate(button['id'], 'visible') is False
    checkbox['name'] = 'renamed'
    assert ExpressionState(doc).evaluate(button['id'], 'visible') is False
    doc['sections'][0]['items'].remove(checkbox)
    doc['sections'][0]['items'].append(create_item('checkbox', {'name': 'use_preview', 'props': {'value': False}}))
    bind_expression_references(doc)
    state = ExpressionState(doc)
    assert state.evaluate(button['id'], 'visible') is True
    assert 'Missing parameter' in state.errors[(button['id'], 'visible')]


def test_rename_clone_and_roundtrip():
    doc, (checkbox, button) = document()
    controller = EditorDocumentController(doc)
    renamed = controller.find_by_id(checkbox['id'])
    renamed['name'] = 'preview_on'
    controller.rename_item_references(checkbox['id'], 'use_preview', 'preview_on')
    current = controller.find_by_id(button['id'])
    assert current['ui']['visible_expression'] == 'preview_on'
    clone = controller.clone_subtree(controller.document['sections'][0])
    child, target = clone['items']
    assert target['ui']['visible_expression'] == child['name']
    assert target['ui']['visible_references'][child['name']] == child['id']
    assert normalize_document(controller.document) == controller.document
    assert rewrite_expression('mode == "mode" || mode_extra', {'mode': 'renamed'}) == 'renamed == "mode" || mode_extra'


def test_reserved_import_and_creation():
    with pytest.raises(ValueError): create_item('checkbox', {'name': 'IF'})
    with pytest.raises(ValueError): normalize_document({'sections': [{'kind': 'folder', 'name': 'else'}]})


def test_limits():
    with pytest.raises(ExpressionError): Expression('!' * 300 + 'true')
    with pytest.raises(ExpressionError): Expression('a' * 4097)
