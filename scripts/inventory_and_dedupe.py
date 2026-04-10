"""
Inventory all files, detect duplicates by MD5 hash, and generate a report.
"""
import os
import hashlib
import json
from collections import defaultdict
from pathlib import Path

BASE = r"C:\Users\Pavlos Elpidorou\Documents\AI Project"
EXCLUDE_DIRS = {"scripts", "__MACOSX", ".git"}
EXCLUDE_EXTS = {".pyc", ".tmp"}

def md5(filepath):
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def scan():
    inventory = []
    hash_map = defaultdict(list)

    for root, dirs, files in os.walk(BASE):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

        for fname in files:
            if fname.startswith("."):
                continue
            fpath = os.path.join(root, fname)
            ext = Path(fpath).suffix.lower()
            if ext in EXCLUDE_EXTS:
                continue

            size = os.path.getsize(fpath)
            fhash = md5(fpath)
            rel_path = os.path.relpath(fpath, BASE)

            entry = {
                "path": rel_path,
                "name": fname,
                "ext": ext,
                "size": size,
                "hash": fhash
            }
            inventory.append(entry)
            if fhash:
                hash_map[fhash].append(rel_path)

    return inventory, hash_map

def main():
    print("Scanning files...")
    inventory, hash_map = scan()
    print(f"Total files scanned: {len(inventory)}")

    # Find duplicates
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    dup_files = sum(len(v) - 1 for v in duplicates.values())
    print(f"Duplicate groups: {len(duplicates)}")
    print(f"Redundant files (can be removed): {dup_files}")

    # Save full inventory
    inv_path = os.path.join(BASE, "scripts", "inventory.json")
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    print(f"Inventory saved to: {inv_path}")

    # Save duplicates report
    dup_path = os.path.join(BASE, "scripts", "duplicates.json")
    with open(dup_path, "w", encoding="utf-8") as f:
        json.dump(duplicates, f, indent=2)
    print(f"Duplicates saved to: {dup_path}")

    # Print duplicate summary
    print("\n--- TOP DUPLICATE GROUPS ---")
    sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for h, paths in sorted_dups[:20]:
        print(f"\n  [{len(paths)} copies] {Path(paths[0]).name}")
        for p in paths:
            print(f"    {p}")

    # Extension breakdown
    from collections import Counter
    ext_count = Counter(e["ext"] for e in inventory)
    print("\n--- FILE TYPES ---")
    for ext, count in ext_count.most_common(15):
        print(f"  {ext or '(no ext)':15s} {count}")

if __name__ == "__main__":
    main()
