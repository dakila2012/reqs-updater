import argparse
import sys
import requests
from packaging.requirements import Requirement
from packaging.version import parse
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_latest_version(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Update pinned package versions in a requirements.txt file to the latest PyPI versions."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="requirements.txt",
        help="The requirements file to update (default: requirements.txt)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying the file"
    )
    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Error reading '{args.file}': {e}", file=sys.stderr)
        sys.exit(1)

    new_lines = []
    updatable_infos = []
    packages_to_fetch = set()

    for line_num, line in enumerate(lines, 1):
        line_stripped = line.rstrip("\n\r")
        has_eol = len(line) > len(line_stripped)
        parts = line_stripped.split("#", 1)
        spec_part = parts[0]
        comment_part = parts[1] if len(parts) > 1 else None
        req_str = spec_part.strip()
        if not req_str or req_str[0] in "-#" or req_str.startswith("--"):
            new_lines.append(line)
            continue
        try:
            req = Requirement(req_str)
        except Exception:
            new_lines.append(line)
            continue
        specs = req.specifier._specs
        if len(specs) != 1 or specs[0]._op != "==":
            new_lines.append(line)
            continue
        name = req.name
        current_version = specs[0]._version

        # Preserve leading and trailing whitespace around spec
        leading_len = len(spec_part) - len(spec_part.lstrip())
        leading_ws = spec_part[:leading_len]
        temp = spec_part[leading_len:]
        trailing_len = len(temp) - len(temp.rstrip())
        trailing_ws = temp[-trailing_len:]

        extras_str = f"[{','.join(sorted(req.extras))}]" if req.extras else ""
        marker_str = f"; {req.marker}" if req.marker else ""

        info = {
            "line_num": line_num,
            "name": name,
            "current_version": current_version,
            "extras_str": extras_str,
            "marker_str": marker_str,
            "leading_ws": leading_ws,
            "trailing_ws": trailing_ws,
            "comment_part": comment_part,
            "has_eol": has_eol,
            "line_stripped": line_stripped,
            "temp_index": len(new_lines),
        }
        new_lines.append(line)
        updatable_infos.append(info)
        packages_to_fetch.add(name)

    package_versions = {}
    if packages_to_fetch:
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_pkg = {executor.submit(get_latest_version, pkg): pkg for pkg in packages_to_fetch}
            for future in as_completed(future_to_pkg):
                pkg = future_to_pkg[future]
                try:
                    latest_str = future.result()
                    if latest_str:
                        package_versions[pkg] = latest_str
                except Exception:
                    print(f"Warning: Could not fetch latest version for {pkg}", file=sys.stderr)

    changes = []
    for info in updatable_infos:
        latest_str = package_versions.get(info["name"])
        if latest_str is None:
            continue
        try:
            latest_version = parse(latest_str)
            if latest_version > info["current_version"]:
                new_req_str = f"{info['name']}{info['extras_str']}=={latest_str}{info['marker_str']}"
                new_spec_part = info["leading_ws"] + new_req_str + info["trailing_ws"]
                if info["comment_part"] is not None:
                    new_stripped = new_spec_part + "#" + info["comment_part"]
                else:
                    new_stripped = new_spec_part
                new_line = new_stripped + ("\n" if info["has_eol"] else "")
                new_lines[info["temp_index"]] = new_line
                changes.append((info["line_num"], info["line_stripped"], new_stripped))
        except Exception:
            print(f"Warning: Invalid latest version {latest_str!r} for {info['name']}", file=sys.stderr)

    if args.dry_run:
        if not changes:
            print("No updates needed.")
        else:
            print("Would make the following changes:")
            for line_num, old, new_ in changes:
                print(f"  line {line_num}: {old} -> {new_}")
    else:
        try:
            with open(args.file, "w", encoding="utf-8", newline="") as f:
                f.writelines(new_lines)
        except OSError as e:
            print(f"Error writing '{args.file}': {e}", file=sys.stderr)
            sys.exit(1)
        if not changes:
            print("No updates needed.")
        else:
            print(f"Updated '{args.file}': {len(changes)} packages updated.")

if __name__ == "__main__":
    main()
