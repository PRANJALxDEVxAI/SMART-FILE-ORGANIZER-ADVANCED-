#!/usr/bin/env python3
"""
Smart File Organizer
--------------------
Organize a folder (default: ~/Downloads) by file type, date, or custom rules.
Nothing is moved unless you pass --apply, so you always get a preview first.
Every applied run is logged so you can undo it.

Usage examples:
    python smart_file_organizer.py organize --by type              # preview only
    python smart_file_organizer.py organize --by type --apply      # really move
    python smart_file_organizer.py organize --by date --apply
    python smart_file_organizer.py init-rules                      # creates organizer_rules.json
    python smart_file_organizer.py organize --by custom --rules organizer_rules.json --apply
    python smart_file_organizer.py undo --preview                  # see what undo would do
    python smart_file_organizer.py undo                            # undo the last run
    python smart_file_organizer.py organize --folder "D:/Stuff" --by type
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HISTORY_NAME = ".organizer_history.json"
SKIP_SUFFIXES = {".crdownload", ".part", ".tmp", ".partial", ".download"}

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".ico", ".tiff"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Code": {".py", ".cpp", ".c", ".h", ".java", ".js", ".ts", ".html", ".css", ".json", ".ipynb", ".sh"},
    "Installers": {".exe", ".msi", ".dmg", ".deb", ".apk", ".iso"},
}

EXAMPLE_RULES = {
    "Screenshots": {"name_contains": ["screenshot", "screen shot"]},
    "Assignments": {"name_contains": ["assignment", "lab", "pps"], "extensions": [".pdf", ".docx", ".cpp"]},
    "Big Files": {"min_size_mb": 500},
    "Photos": {"extensions": [".jpg", ".jpeg", ".png", ".heic"]},
}


# --------------------------------------------------------------------------- #
# Planning helpers
# --------------------------------------------------------------------------- #
def category_by_type(path: Path) -> str:
    ext = path.suffix.lower()
    for name, exts in CATEGORIES.items():
        if ext in exts:
            return name
    return "Other"


def category_by_date(path: Path) -> str:
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return str(Path(str(modified.year)) / f"{modified.month:02d}-{modified.strftime('%B')}")


def category_by_rules(path: Path, rules: dict) -> str:
    """First matching rule wins. A rule matches only if ALL its conditions match."""
    name = path.name.lower()
    ext = path.suffix.lower()
    size_mb = path.stat().st_size / (1024 * 1024)
    for folder, rule in rules.items():
        checks = []
        if "extensions" in rule:
            checks.append(ext in {e.lower() for e in rule["extensions"]})
        if "name_contains" in rule:
            checks.append(any(k.lower() in name for k in rule["name_contains"]))
        if "min_size_mb" in rule:
            checks.append(size_mb >= rule["min_size_mb"])
        if checks and all(checks):
            return folder
    return "Unsorted"


def unique_destination(dst: Path, reserved: set) -> Path:
    """Never overwrite: add ' (1)', ' (2)', ... if the name is taken."""
    candidate, n = dst, 1
    while candidate.exists() or str(candidate) in reserved:
        candidate = dst.with_name(f"{dst.stem} ({n}){dst.suffix}")
        n += 1
    return candidate


def should_skip(path: Path, script_path: Path) -> bool:
    return (
        not path.is_file()
        or path.name.startswith(".")
        or path.name == HISTORY_NAME
        or path.suffix.lower() in SKIP_SUFFIXES
        or path.resolve() == script_path
    )


def build_plan(folder: Path, mode: str, rules: dict | None):
    script_path = Path(__file__).resolve()
    plan, reserved = [], set()
    for item in sorted(folder.iterdir()):
        if should_skip(item, script_path):
            continue
        if mode == "type":
            sub = category_by_type(item)
        elif mode == "date":
            sub = category_by_date(item)
        else:
            sub = category_by_rules(item, rules)
        dst = unique_destination(folder / sub / item.name, reserved)
        reserved.add(str(dst))
        plan.append((item, dst))
    return plan


# --------------------------------------------------------------------------- #
# History (for undo)
# --------------------------------------------------------------------------- #
def load_history(folder: Path) -> list:
    path = folder / HISTORY_NAME
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Warning: history file is corrupted; starting a fresh one.")
        return []


def save_history(folder: Path, history: list) -> None:
    (folder / HISTORY_NAME).write_text(json.dumps(history, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def print_plan(folder: Path, plan) -> None:
    grouped = defaultdict(list)
    for src, dst in plan:
        grouped[dst.parent.relative_to(folder)].append((src, dst))
    for sub in sorted(grouped):
        print(f"\n  {sub}{'/'}  ({len(grouped[sub])} file(s))")
        for src, dst in grouped[sub]:
            note = "" if src.name == dst.name else f"  (renamed to {dst.name})"
            print(f"      {src.name}{note}")


def cmd_organize(args) -> int:
    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Error: '{folder}' is not a folder.")
        return 1

    rules = None
    if args.by == "custom":
        if not args.rules:
            print("Error: --by custom needs --rules <file.json>. Run 'init-rules' to make an example.")
            return 1
        try:
            rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading rules file: {e}")
            return 1

    plan = build_plan(folder, args.by, rules)
    if not plan:
        print("Nothing to organize. The folder is already tidy!")
        return 0

    print(f"Folder: {folder}")
    print(f"Mode:   {args.by}")
    print_plan(folder, plan)
    print(f"\nTotal: {len(plan)} file(s) would be moved.")

    if not args.apply:
        print("\nPREVIEW ONLY - nothing was moved. Re-run with --apply to do it.")
        return 0

    moves, created_dirs, errors = [], [], 0
    for src, dst in plan:
        try:
            if not dst.parent.exists():
                # remember every new directory level so undo can clean them up
                missing = []
                p = dst.parent
                while not p.exists():
                    missing.append(p)
                    p = p.parent
                dst.parent.mkdir(parents=True, exist_ok=True)
                created_dirs.extend(str(m) for m in reversed(missing))
            shutil.move(str(src), str(dst))
            moves.append({"src": str(src), "dst": str(dst)})
        except (OSError, shutil.Error) as e:
            errors += 1
            print(f"  ! Could not move {src.name}: {e}")

    if moves:
        history = load_history(folder)
        history.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": args.by,
            "moves": moves,
            "created_dirs": created_dirs,
        })
        save_history(folder, history)

    print(f"\nDone: moved {len(moves)} file(s), {errors} error(s). Run 'undo' to revert.")
    return 0 if errors == 0 else 2


def cmd_undo(args) -> int:
    folder = Path(args.folder).expanduser().resolve()
    history = load_history(folder)
    if not history:
        print("No history found - nothing to undo.")
        return 0

    entry = history[-1]
    print(f"Last operation: {entry['timestamp']} (mode: {entry['mode']}, {len(entry['moves'])} file(s))")

    reserved, restored, skipped = set(), 0, 0
    for move in reversed(entry["moves"]):
        src, dst = Path(move["src"]), Path(move["dst"])
        if not dst.exists():
            print(f"  - skipped {dst.name}: no longer at {dst.parent.name}/")
            skipped += 1
            continue
        target = unique_destination(src, reserved)
        reserved.add(str(target))
        print(f"  {dst.relative_to(folder)}  ->  {target.name}")
        if not args.preview:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(target))
                restored += 1
            except (OSError, shutil.Error) as e:
                print(f"  ! Could not restore {dst.name}: {e}")
                skipped += 1

    if args.preview:
        print("\nPREVIEW ONLY - nothing was changed. Run 'undo' without --preview to revert.")
        return 0

    # remove folders the organizer created, but only if they are empty now
    for d in sorted(entry.get("created_dirs", []), key=len, reverse=True):
        try:
            Path(d).rmdir()
        except OSError:
            pass

    history.pop()
    save_history(folder, history)
    print(f"\nUndo complete: restored {restored} file(s), skipped {skipped}.")
    return 0


def cmd_init_rules(args) -> int:
    path = Path(args.output)
    if path.exists():
        print(f"'{path}' already exists - not overwriting.")
        return 1
    path.write_text(json.dumps(EXAMPLE_RULES, indent=2), encoding="utf-8")
    print(f"Created {path}. Edit it, then use: organize --by custom --rules {path} --apply")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    default_folder = str(Path.home() / "Downloads")
    parser = argparse.ArgumentParser(description="Smart File Organizer with preview and undo.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_org = sub.add_parser("organize", help="Organize a folder (preview unless --apply).")
    p_org.add_argument("--folder", default=default_folder, help="Folder to organize (default: ~/Downloads)")
    p_org.add_argument("--by", choices=["type", "date", "custom"], default="type")
    p_org.add_argument("--rules", help="JSON rules file for --by custom")
    p_org.add_argument("--apply", action="store_true", help="Actually move the files")
    p_org.set_defaults(func=cmd_organize)

    p_undo = sub.add_parser("undo", help="Undo the last applied organization.")
    p_undo.add_argument("--folder", default=default_folder)
    p_undo.add_argument("--preview", action="store_true", help="Show what undo would do")
    p_undo.set_defaults(func=cmd_undo)

    p_init = sub.add_parser("init-rules", help="Create an example custom rules file.")
    p_init.add_argument("--output", default="organizer_rules.json")
    p_init.set_defaults(func=cmd_init_rules)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())