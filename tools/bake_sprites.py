"""Rebuild characters/<name>/sprites.json from characters/<name>/source.py.

    python tools/bake_sprites.py            # every character with a source.py
    python tools/bake_sprites.py mochi      # just one

The app reads sprites.json; source.py is only the code that draws the
art, so a shared character works even without its source.py.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # for buddyart.py


def bake(folder):
    spec = importlib.util.spec_from_file_location(f"src_{folder.name}", folder / "source.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = {"art": getattr(mod, "ART", 1), "palette": mod.PALETTE,
            "items": [mod.item(i) for i in range(6)], "sprites": mod.SPRITES}
    for section in ("effects", "marks", "props"):          # optional extras
        extra = getattr(mod, section.upper(), None)
        if extra:
            data[section] = extra
    write_sprites(folder / "sprites.json", data)
    return data


def write_sprites(path, data):
    """One sprite row per line, so the art is readable (and diffable) as text."""
    out = ['{', f' "art": {data["art"]},', f' "palette": {json.dumps(data["palette"])},',
           ' "items": [']
    out.append(",\n".join("  " + json.dumps(it) for it in data["items"]))
    out.append(' ],')
    out.append(' "sprites": {')
    entries = []
    for key, rows in data["sprites"].items():
        body = ",\n".join("   " + json.dumps(r) for r in rows)
        entries.append(f'  {json.dumps(key)}: [\n{body}\n  ]')
    out.append(",\n".join(entries))
    out.append(' }')
    for section in ("effects", "marks", "props"):
        if data.get(section):
            out[-1] += ","
            out.append(f' "{section}": {{')
            parts = []
            for key, rows in data[section].items():
                body = ",\n".join("   " + json.dumps(r) for r in rows)
                parts.append(f'  {json.dumps(key)}: [\n{body}\n  ]')
            out.append(",\n".join(parts))
            out.append(' }')
    out.append('}')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    # arguments: character folder names in characters/, or paths to any folder
    folders = []
    for a in sys.argv[1:]:
        p = Path(a)
        folders.append(p if (p / "source.py").exists() else ROOT / "characters" / a.lower())
    if not folders:
        folders = sorted(f for f in (ROOT / "characters").iterdir() if (f / "source.py").exists())
    for folder in folders:
        data = bake(folder)
        print(f"baked {folder.name}: {len(data['sprites'])} sprites")
