## omikuji-scripts

Community scripts for [omikuji](https://github.com/reakjra/omikuji). A script is a single TOML file that describes how to set up a game: pick a prefix, run winetricks, download an installer, run it, register the result in the library. Omikuji renders the inputs as a form, runs the steps, and streams the output.

In omikuji: **+** button, then **Install script**. Local scripts show right away, typing in the search also looks up this repo. Installing a remote script downloads just that script's folder (deletable, tho manually).

> [!WARNING]
> Read the bottom of this README before opening a PR!!!!!

### A script

```toml
[script]
name = "Battle.net"
description = "Downloads the Battle.net installer and runs it"
author = "reakjra"
icon = "./icon.png"
note = "Close the launcher when the installer finishes so the script can continue.\n(also nice pits)."

[[input]]
id = "prefix"
kind = "prefix"
picker = "path"
label = "Wine prefix"

[[step]]
task = "init_prefix"

[[step]]
task = "winetricks"
verbs = ["corefonts"]

[[step]]
task = "download"
url = "https://example.com/Battle.net-Setup.exe"
dest = "${cache}/Battle.net-Setup.exe"

[[step]]
task = "run_exe"
exe = "${cache}/Battle.net-Setup.exe"

[game]
name = "Battle.net"
exe = "${prefix}/drive_c/Program Files (x86)/Battle.net/Battle.net Launcher.exe"
```

### `[script]`

| field | required | notes |
|---|---|---|
| `name` | yes | shown in the browser and as the dialog title |
| `description` | no | brief description of the script under the name |
| `author` | no | display only |
| `icon` | no | relative path to an image in the script folder |
| `note` | no | shown as an info banner before installing, `\n` for line breaks |

### `[[input]]`

Each input becomes a form field. The value is available to steps as `${id}`.

| field | required | notes |
|---|---|---|
| `id` | yes | unique. `cache` and `home` are reserved, `prefix` is only allowed on the prefix kind |
| `kind` | yes | `prefix`, `file`, `directory`, `text`, `choice`, `bool` |
| `label` | yes | field label |
| `picker` | no | prefix kind only: `list` (default, existing prefixes under `prefix_path` setting) or `path` (free path input) |
| `filter` | no | file kind: picker patterns like `"*.exe"` or `"*.tar.gz *.zip"`, `.dll`, etc. |
| `options` | `choice` only | the dropdown values |
| `default` | no | prefilled value, e.g, `"true"`/`"false"` |

At most one `prefix` input. If a script has none, it creates a prefix automatically.

### `[[step]]`

Steps run in order. All string fields support `${variables}`.

| task | fields | what it doess |
|---|---|---|
| `init_prefix` | none | wineboots the prefix, no-op if already initialized |
| `winetricks` | `verbs` | runs `winetricks -q` with the listed verbs |
| `download` | `url`, `dest`, `sha256` (optional) | downloads with progress, verifies the checksum if given |
| `extract` | `archive`, `dest` | unpacks zip, tar.gz, tgz, tar.xz, tar.zst or tar, detected automatically |
| `run_exe` | `exe` | runs the exe through wine and waits for it to exit. |
| `shell` | `run` | runs through `sh -c` with `WINEPREFIX` set, working dir is the cache. Scripts with a shell step show a warning and a red install button |

### `[game]`

Optional. With it, the script registers a library entry when it finishes. Without it its just a silly utility.

| field | required | notes |
|---|---|---|
| `name` | yes | library entry name |
| `exe` | yes | checked after the steps run. If it is missing, omikuji asks the user to locate it |
| `runner` | no | `wine` (default) or `native` |
| `wine_version` | no | runner for the wine steps and the registered game. `"system"` forces system wine. without steps use system wine and the game gets the user's default runner |
| `[game.env]` | no | key/value map merged into the game's launch environment |
| `[game.dll_overrides]` | no | key/value map of wine dll overrides |

### Variables

`${<input id>}` plus three builtins:

| variable | value |
|---|---|
| `${prefix}` | the chosen prefix, or the auto-created one |
| `${cache}` | a scratch folder, deleted after a successful run. |
| `${home}` | the user's home directory |

Unknown variables fail at parse time!

### Contributing

Scripts live at `scripts/<your-github-username>/<script-name>/<script>.toml` with one `.toml` and optionally an icon. 

Fork, add your folder, open a PR. CI validates and merges on its own if valid. If there are any error it'll show

These rules are mandatory in order to make the CI merge your PR:

- files only under `scripts/<your-github-username>/`, verified against the PR author
- exactly one `.toml` per script folder
- allowed files: `.toml`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`
- toml up to 64KB, images up to 1MB
- the icon path must point at a file inside the script folder
- the script must pass the same validation omikuji runs

Test before opening a PR: **+**, **Install script**, **Use local**, pick your toml.
