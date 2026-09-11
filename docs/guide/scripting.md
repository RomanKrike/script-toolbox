# Scripting

Script Toolbox attaches behavior to item **bindings**. A binding connects a supported UI event to a script executed by the active host.

## Script languages

| Host | Supported languages |
| --- | --- |
| Maya | Python, MEL |
| Nuke | Python |
| Houdini | Python, HScript |

Choose the language that matches the host and the task. Python is the portable option across all supported hosts.

## Event model

Items expose only the bindings that make sense for their type. Typical events include click, double-click, value changes, and editing events.

The current configuration contract stores executable behavior in `bindings`. Direct ad-hoc script fields and legacy callback dictionaries are not part of the active schema.

## Referencing items

Script Toolbox distinguishes between internal identity and script-facing naming:

- `id` is the stable internal identity;
- `name` is the symbolic identifier intended for scripts;
- `label` is presentation text.

When a control must be referenced from another control's script, prefer the symbolic `name` rather than presentation text.

## Duplicating scripted blocks

Nested reference rewriting is applied during rename, duplicate, copy, and paste operations. This allows a duplicated block to update supported references to the newly created controls instead of continuing to target the original block.

Automatic rewriting is conservative: direct calls such as `toolbox.get_value("name")` are supported, while aliases, variables, and computed names are not rewritten automatically. When Script Toolbox can identify one of those unresolved cases during rename or Duplicate, the editor shows a warning so the affected scripts can be reviewed manually. Comments and unrelated string literals are ignored.

A practical pattern is to build one complete row or folder, including its internal scripted references, then duplicate that block and customize the copy.

## Embedded code editor

Scripts can be edited directly in the embedded code editor. Keep bindings focused: a UI event should generally call a small operation or dispatch into reusable code rather than contain a large monolithic script.

## Host-specific behavior

Host callbacks are isolated behind the host abstraction so core document behavior remains host-independent. Contributors implementing new host behavior should also read [Host callbacks](../HOST_CALLBACKS.md) and [Architecture](../ARCHITECTURE.md).

## Debugging

When a script does not behave as expected, verify:

1. the correct event binding is configured;
2. the selected language is supported by the current host;
3. referenced item names still exist;
4. the script works in the host's own script console;
5. the toolbox configuration was saved before testing runtime behavior.
