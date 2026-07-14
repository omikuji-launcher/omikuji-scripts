#!/usr/bin/env python3
import sys
import tomllib
from pathlib import Path

TASKS = {
    "init_prefix": [],
    "winetricks": ["verbs"],
    "download": ["url", "dest"],
    "extract": ["archive", "dest"],
    "run_exe": ["exe"],
    "shell": ["run"],
}
KINDS = {"prefix", "file", "directory", "text", "choice", "bool"}
BUILTINS = {"prefix", "cache", "home"}
EXTS = {".toml", ".png", ".jpg", ".jpeg", ".webp", ".svg"}

errors = []


def err(msg):
    errors.append(msg)


def placeholders(s, where):
    out = []
    i = 0
    while True:
        i = s.find("${", i)
        if i == -1:
            return out
        j = s.find("}", i)
        if j == -1:
            err(f"{where}: unterminated ${{ in {s!r}")
            return out
        out.append(s[i + 2:j])
        i = j + 1


def check_script(tag, data):
    meta = data.get("script", {})
    if not str(meta.get("name", "")).strip():
        err(f"{tag}: script.name is missing")

    known = set(BUILTINS)
    prefix_inputs = 0
    for inp in data.get("input", []):
        iid = str(inp.get("id", ""))
        kind = str(inp.get("kind", ""))
        if not iid or iid.startswith(".") or "/" in iid:
            err(f"{tag}: bad input id {iid!r}")
        if iid in known and iid not in BUILTINS:
            err(f"{tag}: duplicate input id {iid!r}")
        if kind not in KINDS:
            err(f"{tag}: unknown input kind {kind!r}")
        if iid in {"cache", "home"} or (iid == "prefix" and kind != "prefix"):
            err(f"{tag}: input id {iid!r} is reserved")
        if kind == "choice" and not inp.get("options"):
            err(f"{tag}: choice input {iid!r} has no options")
        if kind == "prefix":
            prefix_inputs += 1
            if inp.get("picker", "") not in ("", "list", "path"):
                err(f"{tag}: unknown picker {inp.get('picker')!r}")
        elif inp.get("picker"):
            err(f"{tag}: picker is only valid on prefix inputs ({iid!r})")
        known.add(iid)
    if prefix_inputs > 1:
        err(f"{tag}: more than one prefix input")

    templated = []
    for step in data.get("step", []):
        task = str(step.get("task", ""))
        if task not in TASKS:
            err(f"{tag}: unknown task {task!r}")
            continue
        for field in TASKS[task]:
            if field not in step:
                err(f"{tag}: task {task!r} is missing {field!r}")
            elif isinstance(step[field], str):
                templated.append(step[field])

    game = data.get("game")
    if game is not None:
        if not str(game.get("name", "")).strip():
            err(f"{tag}: game.name is missing")
        if not str(game.get("exe", "")).strip():
            err(f"{tag}: game.exe is missing")
        else:
            templated.append(game["exe"])
        if game.get("runner", "") not in ("", "wine", "native"):
            err(f"{tag}: unsupported game.runner {game.get('runner')!r}")
        templated.extend(str(v) for v in game.get("env", {}).values())
        templated.extend(str(v) for v in game.get("dll_overrides", {}).values())

    for text in templated:
        for var in placeholders(text, tag):
            if var not in known:
                err(f"{tag}: unknown variable ${{{var}}}")


def main():
    root = Path(sys.argv[1])
    changed = [l.strip() for l in Path(sys.argv[2]).read_text().splitlines() if l.strip()]
    author = sys.argv[3]

    script_dirs = set()
    for f in changed:
        parts = f.split("/")
        if len(parts) != 4 or parts[0] != "scripts":
            err(f"{f}: files live at scripts/author/script/file, nothing else")
            continue
        _, owner, slug, name = parts
        if owner.lower() != author.lower():
            err(f"{f}: you can only change your own folder ({author}/)")
            continue
        if slug.startswith(".") or not slug:
            err(f"{f}: bad script folder {slug!r}")
            continue
        if Path(name).suffix.lower() not in EXTS:
            err(f"{f}: file type not allowed ({', '.join(sorted(EXTS))})")
            continue
        script_dirs.add((owner, slug))

    titles = []
    for owner, slug in sorted(script_dirs):
        tag = f"{owner}/{slug}"
        d = root / "scripts" / owner / slug
        if not d.is_dir():
            titles.append(slug)
            continue
        tomls = sorted(d.glob("*.toml"))
        if len(tomls) != 1:
            err(f"{tag}: needs exactly one .toml, has {len(tomls)}")
            continue
        toml_path = tomls[0]
        if toml_path.stat().st_size > 64 * 1024:
            err(f"{tag}: {toml_path.name} is over 64KB")
        for asset in d.iterdir():
            if asset.suffix.lower() in EXTS and asset != toml_path and asset.stat().st_size > 1024 * 1024:
                err(f"{tag}: {asset.name} is over 1MB")
        try:
            data = tomllib.loads(toml_path.read_text())
        except Exception as e:
            err(f"{tag}: {e}")
            continue
        titles.append(str(data.get("script", {}).get("name", "")).strip() or slug)
        icon = str(data.get("script", {}).get("icon", ""))
        if icon:
            icon_path = (d / icon).resolve()
            if not icon_path.is_file() or d.resolve() not in icon_path.parents:
                err(f"{tag}: icon {icon!r} not found inside the script folder")
        check_script(tag, data)

    if errors:
        Path("validation_errors.txt").write_text("\n".join(f"- {e}" for e in errors) + "\n")
        print("validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    if titles:
        Path("merge_subject.txt").write_text(f"{author}: {', '.join(titles)}\n")
    print(f"validated {len(script_dirs)} script(s), all good")


if __name__ == "__main__":
    main()
