# Template character: Pip

A working starter buddy (a little blue blob) to copy and turn into your own.

1. Copy this folder into `characters/` and rename it, e.g. `characters/sprout`.
2. In `character.json`, change `"name"` (it must be unique), `"feed_label"`
   and the lines.
3. Change the art in `source.py`, then rebuild `sprites.json`:
   ```
   python tools/bake_sprites.py characters/sprout
   ```
4. Change or delete the example move, scene and hooks in `behaviours.py`
   (or delete the whole file for a buddy with only the built-in behaviours).
5. Restart the buddies. Yours appears under right-click → **Add a buddy**.

| file | what it is | needed? |
|---|---|---|
| `character.json` | name, size, settings, lines | yes |
| `sprites.json` | the art the app draws (made from source.py) | yes |
| `source.py` | the code that draws the art | only for editing art |
| `behaviours.py` | its own moves, scenes and reactions | no |

Keys starting with `_` in `character.json` are notes and are ignored.
The full reference is in `CHARACTERS.md` in the main folder.

This folder isn't in `characters/`, so the app doesn't load it. Pip only
appears if you copy it in.
