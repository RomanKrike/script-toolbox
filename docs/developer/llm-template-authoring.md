# LLM template / preset authoring

This document is the machine-oriented authoring contract for generating Script Toolbox templates with an LLM.

It is intended to be uploaded or pasted into an LLM before asking it to create a preset, reusable UI block, or complete Script Toolbox configuration.

## Scope and terminology

Script Toolbox has one universal Item model. There is no separate item schema for templates.

Use these terms consistently:

- **Preset / template**: one entry in the built-in preset registry. It has metadata plus a root Item subtree.
- **Item subtree**: one ordinary Script Toolbox Item, optionally containing nested Items.
- **Config / document**: a complete importable JSON document with a schema version and top-level sections.

When a user says only "template" or "preset", generate a preset definition unless the request explicitly asks for an importable JSON config.

## Current contract

The current development branch uses configuration schema **21**.

Source of truth:

- scripts/script_toolbox/constants.py — CONFIG_VERSION
- scripts/script_toolbox/model/items.py — universal Item envelope and document normalization
- scripts/script_toolbox/model/item_builtins.py — built-in Item definitions
- scripts/script_toolbox/model/item_definitions/image.py — Image definition
- scripts/script_toolbox/model/bindings.py — binding normalization
- scripts/script_toolbox/core/presets.py — built-in preset metadata contract

If CONFIG_VERSION in source is no longer 21, this document is stale. Do not guess a migration or silently emit an older schema.

Older, newer, or non-empty versionless config documents are rejected by the current loader.

## Preset metadata

A built-in preset entry has this shape:

~~~python
{
    "id": "maya_render_tools",
    "dcc": "maya",
    "category": "RENDER",
    "label": "Render Tools",
    "description": "Common Maya render utilities.",
    "root": {
        # canonical Item subtree
    },
}
~~~

Metadata fields:

| Field | Contract |
| --- | --- |
| id | Stable preset identifier. Must be unique in the preset registry. |
| dcc | One of all, maya, houdini, nuke, blender. Use all only when the entire preset is genuinely host-independent. |
| category | UI grouping label in the Presets tab. Prefer a short uppercase category such as RENDER, SELECTION, CACHE, LOOKDEV, PIPELINE. |
| label | Human-readable preset name. |
| description | Short searchable description / tooltip. |
| root | Ordinary Script Toolbox Item subtree. |

The preset registry accepts blender as metadata even though the currently documented runtime hosts are Maya, Nuke, and Houdini.

For a multi-control preset, prefer a folder root. A preset root is normalized through the same create_item() path as every other Item.

## Canonical Item envelope

Every authored Item must use the schema-21 envelope:

~~~json
{
  "kind": "button",
  "id": "render_settings_button",
  "name": "render_settings",
  "ui": {
    "label": "Render Settings",
    "show_label": true,
    "tooltip": "",
    "width_mode": "auto",
    "width": 120,
    "stretch": 1,
    "alignment": "left",
    "height_mode": "auto",
    "height": 28,
    "vertical_stretch": 1
  },
  "props": {},
  "bindings": []
}
~~~

Containers additionally use an items array.

Do not author flat type properties beside kind. In particular:

- use ui.label, not a root-level label field;
- use props.folder_type, not a root-level folder_type field;
- use props.value, not a root-level value field;
- use props.visible_rows, not a root-level visible_rows field.

Flat or unknown properties are not the canonical schema and may be ignored during normalization.

### Identity

- id is the stable internal identity.
- name is the script-facing symbolic identity.
- ui.label is presentation text only.

Every id and name must be unique within the generated subtree/document.

Use names that are valid symbolic identifiers: letters, digits, and underscores, not starting with a digit. Prefer descriptive snake_case names.

Never reference another Item by label.

## Universal UI fields

All Item kinds support the same ui namespace:

| Field | Allowed values / range | Default |
| --- | --- | --- |
| label | text | Item-specific label |
| show_label | boolean | true |
| tooltip | text | empty |
| width_mode | auto, stretch, fixed | auto |
| width | integer 20..2000 | 120 |
| stretch | integer 1..100 | 1 |
| alignment | left, center, right | left |
| height_mode | auto, stretch, fixed | auto |
| height | integer 8..2000 | 28 |
| vertical_stretch | integer 1..100 | 1 |

Item definitions may override a UI default. For example Column defaults width_mode to stretch, while Icon, Image, Text, and Toggle Icon normally hide the label.

You may omit universal UI fields that should use defaults. For machine-generated reusable presets, explicitly set at least ui.label and any non-default layout behavior.

## Containers and nesting

Current built-in containers:

- folder — container + section
- row — container + layout
- column — container + layout

Only section-capable Items may appear in a complete config's top-level sections array. Among current built-ins, Folder is the section type.

Rows and Columns may contain ordinary Items and other layout containers.

A layout container must not own a section Item. Do not put a Folder directly inside a Row or Column.

A Folder may contain Rows, Columns, controls, display Items, and nested section-capable content where supported by the editor/runtime.

## Built-in Item kinds

### Folder

kind: folder

props:

- folder_type: collapsible | simple | tabs | radio; default collapsible
- collapsed: boolean; default false

Container. Section-capable.

### Row

kind: row

props:

- spacing: integer 0..30; default 4
- equal_widths: boolean; default false
- horizontal_distribution: left | center | right | space_between; default left
- vertical_alignment: top | center | bottom; default center

Container. Horizontal layout.

### Column

kind: column

props:

- spacing: integer 0..30; default 4
- horizontal_alignment: stretch | left | center | right; default stretch
- vertical_distribution: top | center | bottom | space_between; default top

Container. Vertical layout. Default ui.width_mode is stretch.

### Button

kind: button

props:

- color: RGB list of 3 floats in 0..1; default [0.25, 0.25, 0.25]
- icon_path: path string; default empty
- icon_size: integer 8..256; default 18
- icon_only: boolean; default false

Events: click, double_click.

A newly normalized Button receives a default click script binding if an equivalent one is not already present.

### Toggle Button

kind: toggle_button

props:

- state_source: internal | script; default internal
- icon_path: path string
- icon_size: integer 8..256; default 18
- icon_only: boolean
- state_get_script: text
- state_get_language: python | mel
- state_on_script: text
- state_on_language: python | mel | hscript
- state_off_script: text
- state_off_language: python | mel | hscript
- state_on_label: text
- state_off_label: text
- state_on_color: RGB
- state_off_color: RGB
- value: boolean only when state_source is internal

Events: click, double_click.

The default click handler is state_toggle.

### Icon

kind: icon

props:

- path: path string
- width: integer 8..512; default 24
- height: integer 8..512; default 24
- content_alignment: left | center | right; default left

Events: click, double_click.

Default ui.show_label is false.

### Toggle Icon

kind: toggle_icon

props:

- state_source: internal | script
- state_on_path: path string
- state_off_path: path string
- width: integer 8..512
- height: integer 8..512
- content_alignment: left | center | right
- state_get_script: text
- state_get_language: python | mel
- state_on_script: text
- state_on_language: python | mel | hscript
- state_off_script: text
- state_off_language: python | mel | hscript
- value: boolean only when state_source is internal

Events: click, double_click.

Default ui.show_label is false.

### String

kind: string

props:

- value: text

Events: value_changed, editing_finished, click, double_click.

### Integer

kind: integer

props:

- value: integer scalar or vector
- min: integer; default -1000000
- max: integer; default 1000000
- step: integer >= 1; default 1
- size: integer 1..4; default 1
- component_labels: list of labels
- show_slider: boolean

Events: value_changed, editing_finished, click, double_click.

If min is greater than max, normalization swaps them. Value is clamped to the range. Vector values use size components.

### Float

kind: float

props:

- value: numeric scalar or vector
- min: float; default -1000000.0
- max: float; default 1000000.0
- step: float >= 0.000001; default 0.1
- decimals: integer 0..8; default 3
- size: integer 1..4; default 1
- component_labels: list of labels
- show_slider: boolean

Events: value_changed, editing_finished, click, double_click.

### Checkbox

kind: checkbox

props:

- value: boolean
- label_position: left | right; default right

Events: value_changed, click, double_click.

### Menu

kind: menu

props:

- items: list of text values; default ["Option 1", "Option 2"]
- value: one of items

Events: value_changed, click, double_click.

If value is not present in items, normalization selects the first item.

### Color

kind: color

props:

- value: RGB list of 3 floats in 0..1

Events: value_changed, click, double_click.

### Field

kind: field

props:

- source: value | selection; default value
- value: text or list of text
- placeholder: text
- selectable: boolean; default true
- select_scene: boolean; default false
- multiple: boolean; default true
- long_names: boolean; default false
- display_mode: single | list; default list
- visible_rows: integer 1..20; default 4

Events: value_changed, selection_changed, click, double_click.

If multiple is false, display_mode is normalized to single and a list value collapses to its first entry.

### Label

kind: label

props: none.

Events: click, double_click.

### Text

kind: text

props:

- text: multiline text; default "Text"

No public bindings.

Default ui.show_label is false.

### Separator

kind: separator

props: none.

No public bindings.

### Image

kind: image

props:

- source: image path
- fit: contain | cover | stretch; default contain
- width: integer 8..4096; default 200
- height: integer 8..4096; default 120

Events: click, double_click.

Default ui.show_label is false.

## Binding contract

Executable behavior is stored only in bindings.

Canonical script binding:

~~~json
{
  "id": "open_render_settings_click",
  "event": "click",
  "handler": "script",
  "language": "python",
  "script": "mel.eval(\"RenderGlobalsWindow;\")",
  "label": "",
  "mouse_button": "left",
  "modifiers": [],
  "modifier_policy": "exact"
}
~~~

Binding fields:

| Field | Contract |
| --- | --- |
| id | Stable binding identifier. Recommended for authored presets. |
| event | Must be supported by the Item kind. |
| handler | script or state_toggle. state_toggle is valid only for state-toggle Items. |
| language | Persisted bindings accept python, mel, or hscript. The selected language must be supported by the target DCC host. |
| script | Source code. |
| label | Optional editor-facing binding label. |
| mouse_button | left, middle, right for click / double_click. |
| modifiers | Any subset of ctrl, alt, shift. |
| modifier_policy | exact or any. |

For non-mouse events, mouse_button, modifiers, and modifier_policy are omitted by normalization.

Do not use callback dictionaries or direct script fields on the Item root.

## Script language and DCC rules

Prefer Python for generated presets unless the user explicitly requests a host-native language.

Runtime host capabilities:

- Maya: Python and MEL
- Nuke: Python
- Houdini: Python and HScript

Persisted binding languages follow the target host:

- Maya: Python or MEL.
- Nuke: Python.
- Houdini: Python or HScript.

Toggle Button and Toggle Icon **Get State** queries are Python-only in the editor because they must set/evaluate the Python `state` variable. Their **Turn ON** and **Turn OFF** actions may use the native language supported by the target host, including HScript in Houdini.

## Python execution namespace

Python binding code receives toolbox plus host-specific names.

Common:

- toolbox — active Script Toolbox runtime object
- host — active host adapter

Maya:

- cmds
- mel

Nuke:

- nuke
- nukescripts when available

Houdini:

- hou

Use host abstractions when a preset should remain portable across DCCs. Use DCC modules only for host-specific presets.

## Canonical preset example

This example is a Maya-only Render Tools preset using schema-21 Item envelopes:

~~~python
{
    "id": "maya_render_tools",
    "dcc": "maya",
    "category": "RENDER",
    "label": "Render Tools",
    "description": "Open common Maya render UI.",
    "root": {
        "kind": "folder",
        "id": "preset_maya_render_tools_root",
        "name": "maya_render_tools",
        "ui": {
            "label": "Render Tools"
        },
        "props": {
            "folder_type": "simple",
            "collapsed": False
        },
        "bindings": [],
        "items": [
            {
                "kind": "button",
                "id": "preset_maya_render_settings",
                "name": "render_settings",
                "ui": {
                    "label": "Render Settings"
                },
                "props": {},
                "bindings": [
                    {
                        "id": "preset_maya_render_settings_click",
                        "event": "click",
                        "handler": "script",
                        "language": "python",
                        "script": "mel.eval(\"RenderGlobalsWindow;\")"
                    }
                ]
            }
        ]
    }
}
~~~

The normalizer fills omitted default UI, props, and mouse-binding fields.

## Complete importable config

When the user explicitly asks for a JSON config that can be imported, output a complete document:

~~~json
{
  "version": 21,
  "sections": [
    {
      "kind": "folder",
      "id": "render_tools_root",
      "name": "render_tools",
      "ui": {
        "label": "Render Tools"
      },
      "props": {
        "folder_type": "simple",
        "collapsed": false
      },
      "bindings": [],
      "items": []
    }
  ]
}
~~~

Rules:

- version must be 21 for this contract.
- sections must be a list.
- each top-level entry must be section-capable; currently use folder.
- JSON must contain no comments and no trailing commas.
- do not emit a versionless non-empty document.
- do not invent migrations from older schemas.

## LLM generation procedure

When asked to create a Script Toolbox template:

1. Determine the target DCC: maya, nuke, houdini, all, or another registry-supported target explicitly requested by the user.
2. Decide whether the requested output is a preset definition, an Item subtree, or a complete config.
3. Choose only registered Item kinds from this document.
4. Build the Item tree using the canonical kind / id / name / ui / props / bindings envelope.
5. Put children only under container Items.
6. Give every Item a unique id and name.
7. Use Python by default. Use MEL only for Maya when requested or materially simpler.
8. Use bindings only on events supported by that Item kind.
9. Keep scripts small. Prefer toolbox and host APIs for reusable behavior.
10. Validate references: scripts should target Item names, never labels.
11. If duplicatable blocks reference sibling Items, use direct literal toolbox calls where possible so Script Toolbox can rewrite supported references during clone / duplicate.
12. Return only the requested artifact unless the user asks for explanation.

## Validation checklist

Before emitting a template, verify:

- preset id is unique and dcc metadata is valid;
- config version is exactly 21 when outputting a full document;
- every kind is supported;
- every Item has id, name, ui, props, bindings;
- container children use items;
- Row / Column do not directly contain Folder sections;
- Item names are symbolic and unique;
- scripts reference name, not ui.label;
- props are nested under props;
- presentation values are nested under ui;
- bindings use supported events;
- binding languages match the target host (Maya: Python/MEL, Nuke: Python, Houdini: Python/HScript);
- menu value exists in menu items;
- numeric vector size is 1..4;
- RGB values contain exactly 3 values in 0..1;
- Field visible_rows is 1..20;
- Image dimensions are 8..4096;
- JSON output has no Python booleans, comments, or trailing commas.

## Do not invent

An LLM must not invent:

- new Item kinds;
- new props;
- new event names;
- new binding handlers;
- root-level aliases for ui or props;
- compatibility fields from older schemas;
- migration behavior;
- unsupported script languages in persisted bindings.

If a requested feature cannot be represented with the current Item registry, say which missing capability would require a new Item type or plugin code instead of fabricating schema fields.

## Repository-aware mode

If the LLM has access to the Script Toolbox repository, this document is guidance, not a substitute for source verification.

Before authoring against a newer revision, inspect:

1. scripts/script_toolbox/constants.py
2. scripts/script_toolbox/model/item_builtins.py
3. scripts/script_toolbox/model/item_definitions/
4. scripts/script_toolbox/model/items.py
5. scripts/script_toolbox/model/bindings.py
6. scripts/script_toolbox/core/presets.py

If source and this document disagree, report the discrepancy and follow the current source contract.