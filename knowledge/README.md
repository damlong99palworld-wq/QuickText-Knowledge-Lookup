# Knowledge Lookup

Standalone Windows desktop app for personal technical notes — especially Unreal Engine 5, Blueprint, GAS, Niagara, animation, and AI terms.

This version is **not** integrated into QuickText. Keep it separate until the data model and search are stable.

## Requirements

- Python 3.10+
- PySide6
- rapidfuzz (recommended; difflib is used if it is missing)

## Install

```bat
cd knowledge_lookup
py -3 -m pip install -r requirements.txt
```

Linux / macOS:

```bash
cd knowledge_lookup
python3 -m pip install -r requirements.txt
```

## Run

```bat
py -3 main.py
```

```bash
python3 main.py
```

Useful flags:

```bat
py -3 main.py --seed-sample
py -3 main.py --query "niagara"
py -3 main.py --data-dir D:\Temp\KnowledgeLookup
```

`--query` is the future QuickText hook. QuickText can later launch this app with selected text.

## Data location

Windows:

```
%APPDATA%\KnowledgeLookup\knowledge.json
%APPDATA%\KnowledgeLookup\settings.json
%APPDATA%\KnowledgeLookup\knowledge.backup.json
```

Linux / this environment:

```
~/.local/share/KnowledgeLookup/
```

Override with `KNOWLEDGE_LOOKUP_DIR` or `--data-dir`.

Before every save the previous file is copied into rotating backups:

- `knowledge.backup.json`
- `knowledge.backup.2.json`
- `knowledge.backup.3.json`

If `knowledge.json` is invalid, the app tries backups first and copies the broken file to `knowledge.corrupted.json`. It does not delete user data.

A first run with an empty store imports `sample/knowledge.sample.json`.

## Reading appearance

Settings → Appearance:

- Styles per group: Entry Name, Description, Property Name, Property Value, Category, Tags
- Font family (system fonts), size 8–40, Bold / Italic / Underline, default color
- Line spacing, paragraph spacing, property spacing, reading width
- Presets: Compact / Default / Comfortable / Large Text
- Theme: Dark / Light / System
- Live preview
- Zoom display only: Ctrl+= / Ctrl+- / Ctrl+0 (does not change saved font sizes)

Property editor → Style... stores **overrides only**. Empty style follows the global Appearance. Reset Style to Default clears overrides.

Entry `color` and property `style.color` / `value_color` use the same Saved Colors list as the entry color picker.

## Colors (QuickText-compatible)

Each entry has optional `color` as `#rrggbb` (same as QuickText snippets). Empty string = default UI text color.

- Color button in Add/Edit opens the picker: mixer, preview, HEX, Saved swatches (max 16, newest first, no duplicates), Save swatch, Clear (Default), screen eyedropper.
- Only the entry **name** is colored (list + Quick View title).
- `saved_colors` is in `settings.json` for standalone use. Later merge with QuickText should share this same list/format — not a second palette.
- Old JSON without `color` loads as `""`. Duplicate copies color. Import/Export keep `color`.

## V1.1 standalone workflow

Default global hotkey: **Ctrl+F2** (change in Settings).

Windows only for global hotkey + selected-text capture (`RegisterHotKey` + synthetic Ctrl+C). No extra pip packages.

### Settings

File → Settings or `Ctrl+,`

- Global Lookup Hotkey
- Capture selected text when opened
- Restore clipboard after capture
- Focus search when no selected text
- Popup near mouse / screen center
- Minimize to tray when closed
- Start minimized to tray

Settings persist in `%APPDATA%\KnowledgeLookup\settings.json`. Changing the hotkey unregisters the old combo and registers the new one without restart.

Closing the window hides to tray. **Exit** from the tray or File → Exit quits.

### Test selected text

1. Keep the app running (tray is fine).
2. In Chrome / VS Code / UE / Notepad, select `Gameplay Tag`.
3. Press **Ctrl+F2**.
4. Search should fill with `Gameplay Tag` and open that entry.

No selection + hotkey: window opens, search focused, no crash.

Unmatched text: "No matching Knowledge Entry found." + **+ Create Knowledge** (Name prefilled).

### Test clipboard restore

1. Copy `MY OLD CLIPBOARD`.
2. Select `Gameplay Ability`.
3. Press the hotkey.
4. Paste in Notepad — must still be `MY OLD CLIPBOARD`.

V1.1 restores **plain text** only. HTML / images / files on the clipboard are not snapshotted.

### `--query`

```bat
py -3 main.py --query "motion warping"
```

Independent of the hotkey. Still used when another app launches Knowledge Lookup.

### Limits

- Global hotkey and Ctrl+C capture work on **Windows**.
- Some apps block synthetic Ctrl+C or copy slowly; raise `capture_delay_ms` in settings.json if needed (40–800).
- Protected UIs (some games, elevated windows) may not copy.
- If Ctrl+F2 is taken, the app warns and keeps running; pick another combo.

## V1 features

- Add / edit / delete / duplicate knowledge entries
- Core fields: Name, Aliases, Category, Short Description, Tags
- Custom properties with suggested names
- Rename, delete, move property up/down
- Multiline property values
- Quick read-only view + Edit dialog
- Copy name / description / property / all
- Case-insensitive search across name, aliases, description, category, tags, property names and values
- Fuzzy search (`niagra` → Niagara, `game ability` → Gameplay Ability)
- Dark theme
- Keyboard: search focused on start, `↓` / `Enter` / `Esc`, `Ctrl+N` add, `Ctrl+E` edit, `Ctrl+D` duplicate
- Import / Export JSON from the File menu

## Architecture

```
knowledge_lookup/
├── main.py                 run this
├── app.py                  CLI + LookupApp (hotkey → capture → search)
├── constants.py            APP_NAME, data filenames, DEFAULT_HOTKEY
├── models/                 dataclasses only
│   ├── knowledge.py
│   ├── property.py
│   └── settings.py
├── services/               no widgets
│   ├── storage.py          JSON + backup
│   ├── search.py           exact + fuzzy
│   ├── hotkeys.py          Windows RegisterHotKey
│   ├── clipboard.py
│   └── selection_capture.py
├── shared/                 reuse later with QuickText
│   ├── color_system.py     #rrggbb + saved swatches
│   ├── appearance.py       reading styles / presets
│   └── ui_helpers.py       apply font/color to widgets
├── ui/                     windows and dialogs
├── sample/knowledge.sample.json
└── requirements.txt
```

IDs are independent of names (`knowledge_…`, `prop_…`) so entries can be renamed and later linked as Related Concepts.

## Package as .exe (Windows)

```bat
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --noconsole --onefile --name KnowledgeLookup ^
  --add-data "sample/knowledge.sample.json;sample" ^
  main.py
```

On Linux the `--add-data` separator is `:` instead of `;`.

Output: `dist/KnowledgeLookup/KnowledgeLookup.exe`

The packaged app still writes live data under `%APPDATA%\KnowledgeLookup\`, not next to the exe.

## Later (not now)

- QuickText integration / shared hotkey
- Knowledge graph / ID links
- AI assist that never auto-saves
