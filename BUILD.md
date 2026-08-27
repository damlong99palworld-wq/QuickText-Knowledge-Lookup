# Build QuickText.exe (Windows)

This project stays multi-file. PyInstaller bundles it from `main.py` into a single windowed EXE.

User data is **not** stored next to the EXE. Runtime files stay in:

```text
%APPDATA%\QuickText\
```

Upgrading the EXE does not wipe snippets or knowledge.

## Requirements on the build PC

- Windows 10/11 64-bit
- Python 3.11 or 3.12 (64-bit), with `py` launcher
- Internet once (to install pip packages)

This Linux/dev environment cannot emit a real Windows EXE. Run `build.bat` on Windows.

## Build

```bat
cd QuickText
build.bat
```

Output:

```text
QuickText\dist\QuickText.exe
```

Equivalent command:

```bat
py -3 -m pip install -r requirements-build.txt
py -3 -m PyInstaller --noconfirm --clean QuickText.spec
```

## What is bundled

- App source (`main.py`, `app.py`, `ui\`, `services\`, `models\`, `knowledge\`)
- `data\defaults.json`
- `knowledge\sample\knowledge.sample.json` (first-run seed if the user has no entries)
- PySide6 `QtCore` / `QtGui` / `QtWidgets`
- `platforms\qwindows.dll`
- `rapidfuzz`

## What is excluded

Unused Qt modules (WebEngine, QML, Multimedia, 3D, Charts, SQL, Bluetooth, …) and most unused Qt plugins/translations.

Audit of this tree only imports:

- `PySide6.QtCore`
- `PySide6.QtGui`
- `PySide6.QtWidgets`
- `rapidfuzz`
- stdlib + `ctypes` / `winreg`

## UPX

Default spec has `upx=False`.

If UPX is installed and you want a size comparison:

1. Copy `QuickText.spec` to `QuickText-upx.spec`
2. Set `upx=True` on the `EXE(...)` block
3. Build and compare `dist\QuickText.exe`

Skip UPX if Defender flags the file or the EXE fails to start. Qt DLLs often compress poorly and can trigger AV.

## Frozen resource paths

`services/paths.py` uses `sys._MEIPASS` when frozen so bundled JSON is found.

## After build — test checklist

1. Double-click `QuickText.exe` (no console).
2. Tray icon appears.
3. `Ctrl+F1` opens Palette.
4. Palette **Knowledge** pastes clipboard/search into Knowledge Lookup.
5. Manager **Knowledge** (right of Load Profile) opens Knowledge.
6. Snippet paste and snippet hotkeys work.
7. Knowledge add/edit/delete + fuzzy search work.
8. Restart EXE — data still in `%APPDATA%\QuickText\`.
9. Tray Exit ends the process.

Best test: copy `QuickText.exe` to a PC / VM / Windows Sandbox with **no Python**.

## Typical size

A trimmed PySide6 onefile app is usually **~40–80 MB**. Most of that is Qt6Core/Gui/Widgets. Do not rewrite the UI toolkit only to shrink a few MB.

## Troubleshooting

| Symptom | What to try |
|---|---|
| EXE starts then exits | Run `py -3 main.py` from source first. Check `%TEMP%` PyInstaller logs. Temporarily set `console=True` in the spec. |
| Missing `qwindows` | Confirm `platforms/qwindows` was not filtered out of binaries. |
| No sample knowledge | Confirm `knowledge/sample/knowledge.sample.json` is listed under `datas` in the spec. |
| Fuzzy search broken | Keep `hiddenimports` for `rapidfuzz`. |
| Hotkeys fail | Run as a normal user desktop session, not a service. |
| AV quarantine | Rebuild with `upx=False`, sign the EXE if you have a cert. |

## Clean

```bat
rmdir /s /q build dist
del /q QuickText.spec.bak
```

Do not ship `build\`, `__pycache__`, or `.pyc`. Ship `QuickText.exe` (+ this file if you want).
