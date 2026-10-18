# Smart File Organizer

A small Python command-line tool that tidies a messy folder (like Downloads) by **file type**, **date**, or **your own custom rules**. It always shows a **preview** before moving anything, and you can **undo** the last run.

Built with only the Python standard library (`pathlib`, `shutil`, `json`, `argparse`), so there is nothing to install.

## Features

- **Preview mode by default**: nothing moves unless you pass `--apply`
- **Three ways to organize**: by file type, by modified date, or by custom rules
- **Undo**: reverts the last organization and removes the empty folders it created
- **Safe**: never overwrites files (duplicates become `name (1).ext`), and skips hidden files, unfinished downloads (`.crdownload`, `.part`, `.tmp`) and the script itself
- **No dependencies**: just Python 3.10+

## Requirements

- Python 3.10 or newer (check with `python --version`, or `py --version` on Windows)

## Setup

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Run the commands below. Use `py` instead of `python` on Windows if `python` isn't found.

```bash
git clone https://github.com/<your-username>/smart-file-organizer.git
cd smart-file-organizer
```

## Usage

The general pattern is:

```
python main.py <command> [options]
```

If you don't pass `--folder`, it uses your `Downloads` folder.

### 1. Preview (nothing is moved)

```bash
python main.py organize --by type
python main.py organize --folder "C:/Users/YourName/Downloads" --by type
```

### 2. Organize for real

Add `--apply` once the preview looks right:

```bash
python main.py organize --by type --apply
```

### 3. Undo the last run

```bash
python main.py undo --preview    # see what undo would do
python main.py undo              # actually undo it
```

Undo only reverses the **most recent** run, and skips any file you have moved or deleted since.

## Organizing modes

| Option | What it does | Example result |
| --- | --- | --- |
| `--by type` | Groups by file extension | `Images/`, `Documents/`, `Archives/`, `Code/` |
| `--by date` | Groups by last-modified date | `2026/10-October/` |
| `--by custom` | Uses rules from a JSON file | `Assignments/`, `Screenshots/` |

### File type categories

| Folder | Extensions |
| --- | --- |
| Images | jpg, jpeg, png, gif, bmp, webp, svg, heic, ico, tiff |
| Videos | mp4, mkv, avi, mov, wmv, flv, webm |
| Audio | mp3, wav, flac, aac, ogg, m4a |
| Documents | pdf, doc, docx, txt, rtf, odt, md, epub |
| Spreadsheets | xls, xlsx, csv, ods |
| Presentations | ppt, pptx, odp |
| Archives | zip, rar, 7z, tar, gz, bz2 |
| Code | py, cpp, c, h, java, js, ts, html, css, json, ipynb, sh |
| Installers | exe, msi, dmg, deb, apk, iso |
| Other | anything not listed above |

You can edit the `CATEGORIES` dictionary in `main.py` to add or change these.

## Custom rules

Create an example rules file:

```bash
python main.py init-rules
```

This creates `organizer_rules.json`:

```json
{
  "Screenshots": { "name_contains": ["screenshot", "screen shot"] },
  "Assignments": {
    "name_contains": ["assignment", "lab", "pps"],
    "extensions": [".pdf", ".docx", ".cpp"]
  },
  "Big Files": { "min_size_mb": 500 },
  "Photos": { "extensions": [".jpg", ".jpeg", ".png", ".heic"] }
}
```

Then use it:

```bash
python main.py organize --by custom --rules organizer_rules.json --apply
```

How rules work:

- The key (like `"Assignments"`) is the folder name files will be moved into.
- A rule can use `extensions`, `name_contains` and `min_size_mb`.
- A file matches a rule only if it meets **all** the conditions in that rule.
- Rules are checked from top to bottom and the **first match wins**.
- Files that match no rule go into `Unsorted/`.

## All commands

| Command | Description |
| --- | --- |
| `organize` | Plan (and optionally apply) an organization |
| `undo` | Revert the last applied organization |
| `init-rules` | Create an example `organizer_rules.json` |

| Option | Used with | Description |
| --- | --- | --- |
| `--folder PATH` | `organize`, `undo` | Folder to work on (default: `~/Downloads`) |
| `--by {type,date,custom}` | `organize` | How to organize (default: `type`) |
| `--rules FILE` | `organize` | JSON rules file for `--by custom` |
| `--apply` | `organize` | Actually move files (otherwise preview only) |
| `--preview` | `undo` | Show what undo would do without doing it |
| `--output FILE` | `init-rules` | Name of the rules file to create |

## How undo works

Every time you run `organize --apply`, the tool saves a log of each move in a hidden file called `.organizer_history.json` inside the organized folder. `undo` reads the latest entry, moves each file back, removes any empty folders it created, and deletes that entry from the log.

## Safety notes

- Always run a preview first.
- Test on a small folder before using it on one with important files.
- Files are only moved, never deleted or overwritten.

## What I learned

- Working with files and folders using `pathlib`
- Moving files safely with `shutil`
- Reading file metadata (modified time, size, extension)
- Building a command-line tool with `argparse`
- Writing safe automation with preview and undo

## License

MIT. Feel free to use and modify.
