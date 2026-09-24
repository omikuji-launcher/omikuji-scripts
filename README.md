## omikuji-scripts

Community scripts for [omikuji](https://github.com/omikuji-launcher/omikuji). A script is a single TOML file that describes how to set up a game: pick a prefix, run winetricks, download an installer, run it, register the result in the library. Omikuji renders the inputs as a form, runs the steps, and streams the output.

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
| `kind` | yes | `prefix`, `runner`, `file`, `directory`, `text`, `choice`, `bool` |
| `label` | yes | field label |
| `picker` | no | prefix kind only: `list` (default, existing prefixes under `prefix_path` setting) or `path` (free path input) |
| `filter` | no | file kind: picker patterns like `"*.exe"` or `"*.tar.gz *.zip"`, `.dll`, etc. |
| `options` | `choice` only | the dropdown values |
| `default` | no | prefilled value, e.g, `"true"`/`"false"` |

At most one `prefix` input. If a script has none, it creates a prefix automatically.

At most one `runner` input too: the user picks one of their installed runners and it runs both the script steps and the registered game. Can't be combined with `wine_version`, pick one.

### `[[step]]`

Steps run in order. All string fields support `${variables}`.

| task | fields | what it doess |
|---|---|---|
| `init_prefix` | none | wineboots the prefix, no-op if already initialized |
| `winetricks` | `verbs` | runs `winetricks -q` with the listed verbs |
| `download` | `url` or `url_from` + `url_match`, `dest`, `sha256` (optional) | downloads with progress, verifies the checksum if given. `url_from` looks the link up instead of hardcoding it, see [Links that change](#links-that-change) |
| `extract` | `archive`, `dest` | unpacks zip, tar.gz, tgz, tar.xz, tar.zst or tar, detected automatically |
| `run_exe` | `exe`, `dll_overrides` (optional) | runs the exe through wine and waits for it to exit. `dll_overrides` is a key/value map applied as `WINEDLLOVERRIDES` for that run only |
| `shell` | `run` | runs through `sh -c` with `WINEPREFIX` set, working dir is the cache. Scripts with a shell step show a warning and a red install button |

Any step can also carry a `when`, see [Conditions](#conditions).

### Conditions

Any `[[step]]` or game can carry a `when` table. It only runs (or registers) when every listed input equals its value:

```toml
[[step]]
task = "download"
url = "https://.../launcher-global.exe"
dest = "${cache}/launcher.exe"
when = { region = "Global" }
```

Keys are input ids, values are what to match (for a `choice`, one of its `options`). Multiple keys all have to match. Anything with no `when` always runs.

### Links that change

plenty of vendors put the version in the installer filename, or sign the link with a token that expires. Hardcoding either means the script breaks on the next release and you get a 404 or a 403 (we don't want that do we?)

`url_from` points at a page that always mentions the current link, and `url_match` is a regex that pulls it out. The first match wins.

```toml
[[step]]
task = "download"
url_from = "https://www.perfectworld.com/public/commonData/gamesData/gameDownload/nte-gameDownload.js"
url_match = 'https://ntecdn\d*\.perfectworld\.com/[^"]+\.exe'
dest = "${cache}/nte-setup.exe"
```

`url_match` is a regex and is not template expanded, so `${}` in it stays literal.

#### Anchor the regex to the vendor's own host.

a lazy `https://[^"]+\.exe` on a page that lists several downloads grabs whichever comes first, and that is often a third party mirror or an unrelated client. Keep the query string too when the link is signed, dropping it gets you a 403. 

> Single quotes around the regex, TOML treats those as literal strings and won't eat your backslashes!

### Exes resolve

Some installers let the user pick any folder, so `${prefix}/drive_c/Program Files/...` is a guess that fails the moment someone installs somewhere else, and it's not ideal at all anyway. `exe_from_registry` reads the install location back out of the prefix instead:

```toml
[game]
name = "HoYoPlay"
exe_from_registry = "HYP_1_0_global"
```

The value is the uninstall key name, the last part of `Software\Microsoft\Windows\CurrentVersion\Uninstall\<name>`.

how it resolves, in order:

\- looks in both `system.reg` and `user.reg`, and in both the plain and `Wow6432Node` views. Keys with no values are skipped, an uninstall usually leaves an empty one behind

\- if the key has a `DisplayIcon` pointing at an `.exe`, that's the answer. Surrounding quotes and a trailing `,0` icon index are stripped

\- otherwise it takes the install folder from `InstallLocation`, else the folder of `DisplayIcon`, else the folder of `UninstallString`, and joins the relative `exe` you declared

\- also the result is checked. If nothing is there, omikuji asks the user to locate it, same as a wrong hardcoded path

! When `DisplayIcon` is an icon file rather than an exe, declare a relative `exe` alongside the key:

```toml
[game]
name = "Netmarble Launcher"
exe_from_registry = "ebab0fa0-3e67-5055-898a-0b6ee5815a99"
exe = "Netmarble Launcher.exe"
```

That `exe` has to be relative, it's joined onto whatever folder the registry gives back.

some key names are readable (`NTEGlobal`, `StoveLauncher`), some are a hash or a GUID, and some are a leftover from a rebrand that never happened, hello stupid ass `Uplay`. I'm fairly sure they're tied to the product, so they won't change in any context unless they changed it themselves, which shouldn't be common hopefully.

#### Getting the key!

install the thing once through your own script, let the launcher open at the end (a few installers only write the key at that point), then read it back out:

```fish
awk '/^\[.*Uninstall\\\\/ { k=$0; sub(/^.*Uninstall\\\\/,"",k); sub(/\].*$/,"",k) } /^"DisplayIcon"=/ { print k "  " $0 }' /yourprefix/system.reg
```

run it against `user.reg` too, some installers write there instead. Find the line whose path points at the launcher, and the key is what's in front of it. If wine hasn't flushed yet the file can lag a minute or so behind, so if it's not there, wait a bit and look again, not sure what exactly triggers it, but for example as far as i can tell some launchers, when closing the installer without letting it open the launcher/application, they wont register anything.

### `[game]` / `[[game]]`

Optional. With it, the script registers a library entry when it finishes. Without it its just a silly utility.

Use a single `[game]` table, or several `[[game]]` blocks with `when` to register a different game per branch. The first game whose `when` matches wins:

```toml
[[game]]
name = "Arknights (Global)"
exe = "${prefix}/drive_c/Program Files/YostarGames/Arknights_EN_Gamelauncher/Arknights_EN_Gamelauncher.exe"
when = { region = "Global" }

[[game]]
name = "Arknights (CN)"
exe = "${prefix}/drive_c/Program Files/Hypergryph Launcher/Launcher.exe"
when = { region = "CN" }
```

| field | required | notes |
|---|---|---|
| `name` | yes | library entry name |
| `exe` | yes, unless `exe_from_registry` | checked after the steps run. If it is missing, omikuji asks the user to locate it |
| `exe_from_registry` | no | uninstall key name, used when the install folder isn't predictable, see [Exes resolve](#exes-resolve) |
| `runner` | no | `wine` (default) or `native` |
| `wine_version` | no | runner for the wine steps and the registered game. `"system"` forces system wine. without steps use system wine and the game gets the user's default runner |
| `when` | no | with `[[game]]`, only register this one when the inputs match, see [Conditions](#conditions) |
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

- files only under `scripts/<your-github-username>/`, verified against the PR author, unless you're [editing someone else's script](#editing-someone-elses-script)
- exactly one `.toml` per script folder
- allowed files: `.toml`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`
- toml up to 64KB, images up to 1MB
- the icon path must point at a file inside the script folder
- the script must pass the same validation omikuji runs

Test before opening a PR: **+**, **Install script**, **Use local**, pick your toml.

#### Editing someone else's script

A PR can change another author's script, as long as it touches only that one script folder. CI validates it as usual, but instead of merging it tags the owner, and it merges once the owner comments `/approve` on the PR.

- only the folder owner's `/approve` counts, and the comment has to be exactly `/approve`

Yeah pretty obvious.
