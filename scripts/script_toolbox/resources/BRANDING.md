# Script Toolbox icons

The approved FigCraft layouts are the source of these assets:

- `logo_sbt.*`: layout **02**, orange cube with white `St`.
- `logo_sbt_monochrome.*`: layout **02.1**, outlined monochrome cube with white `St`.

Each variant is provided as SVG, a transparent 1024 px PNG, and a Windows ICO
containing 16, 20, 24, 32, 40, 48, 64, 96, 128 and 256 px images. Small ICO images
use 32-bit DIB data; the 256 px image uses PNG. All sizes have transparency.
PNG/ICO exports fit the artwork inside a square with consistent optical padding;
the original SVG proportions and lettering are preserved.

The color ICO remains at the existing `logo_sbt.ico` path. Plugin windows and the
standalone QApplication use it through `style.application_icon()`. The existing
Windows build workflows embed the same file into `ScriptToolbox.exe`.

For a monochrome integration, use the optional argument:

```python
from script_toolbox.style import application_icon, apply_window_icon

icon = application_icon(monochrome=True)
apply_window_icon(window, monochrome=True)
```

The two variants are cached independently. The default stays color, including on
existing calls to these helpers. No DCC host application's global icon is changed.
