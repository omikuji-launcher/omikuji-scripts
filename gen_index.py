#!/usr/bin/env python3
import json
import subprocess
import sys
import tomllib
from pathlib import Path

root = Path(__file__).parent
scripts_root = root / "scripts"
entries = []

for author_dir in sorted(p for p in scripts_root.iterdir() if p.is_dir() and not p.name.startswith(".")):
    for script_dir in sorted(p for p in author_dir.iterdir() if p.is_dir()):
        tomls = sorted(script_dir.glob("*.toml"))
        if not tomls:
            continue
        toml_path = tomls[0]
        try:
            data = tomllib.loads(toml_path.read_text())
        except Exception as e:
            print(f"skipping {toml_path}: {e}", file=sys.stderr)
            continue
        meta = data.get("script", {})
        if not meta.get("name"):
            print(f"skipping {toml_path}: no script.name", file=sys.stderr)
            continue

        icon_rel = ""
        icon = meta.get("icon", "")
        if icon:
            icon_path = (script_dir / icon).resolve()
            if icon_path.is_file() and root.resolve() in icon_path.parents:
                icon_rel = icon_path.relative_to(root.resolve()).as_posix()

        try:
            modified = subprocess.check_output(
                ["git", "log", "-1", "--format=%cs", "--", str(script_dir)],
                cwd=root, text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            modified = ""

        entries.append({
            "author": author_dir.name,
            "slug": script_dir.name,
            "name": meta["name"],
            "description": meta.get("description", ""),
            "has_shell": any(s.get("task") == "shell" for s in data.get("step", [])),
            "modified": modified,
            "toml": toml_path.relative_to(root).as_posix(),
            "icon": icon_rel,
        })

(root / "index.json").write_text(json.dumps(entries, indent=2) + "\n")
print(f"indexed {len(entries)} scripts")
