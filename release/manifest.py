#!/usr/bin/env python3
"""Release contract used by all LMFT publishing workflows.

No network access or credentials. The contract is intentionally much smaller
than Terra Rasa's per-Minecraft-version publishing matrix: one universal
runtime jar for each of Fabric and NeoForge.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]


def config():
    version = (ROOT / "release/VERSION").read_text(encoding="utf-8").strip()
    target = json.loads((ROOT / "release/targets.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError(f"Invalid release version {version!r}")
    versions = target["minecraft_versions"]
    if not versions or len(versions) != len(set(versions)):
        raise ValueError("Minecraft targets must be nonempty and unique")
    if target["loaders"] != ["fabric", "neoforge"]:
        raise ValueError("This release contract requires Fabric and NeoForge")
    if target["compilation_target"] not in versions:
        raise ValueError("Compilation target missing from the support matrix")
    return version, target


def channel(version):
    lowered = version.lower()
    if "-alpha" in lowered:
        return "alpha"
    if "-beta" in lowered or "-rc" in lowered:
        return "beta"
    return "release"


def jar_name(version, loader):
    if loader not in ("fabric", "neoforge"):
        raise ValueError(f"Unexpected loader {loader!r}")
    return f"lmft-{loader}-26.x-{version}+26.x.jar"


def notes(version):
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    marker = f"## {version}"
    lines = changelog.splitlines()
    indices = [i for i, line in enumerate(lines) if line == marker]
    if len(indices) != 1:
        raise ValueError(f"Missing or ambiguous changelog heading {marker!r}")
    i = indices[0]
    j = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    result = "\n".join(lines[i + 1:j]).strip() + "\n"
    if len(result.strip()) < 30:
        raise ValueError("Release notes must be substantial")
    return result


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("version", "channel", "file", "stage", "verify", "notes", "games"))
    parser.add_argument("--loader", choices=("fabric", "neoforge"))
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag")
    args = parser.parse_args()
    version, target = config()
    if args.tag and args.tag != f"v{version}":
        raise ValueError(f"Tag {args.tag!r} does not match release/VERSION v{version}")
    if args.action == "version":
        print(version)
    elif args.action == "channel":
        print(channel(version))
    elif args.action == "file":
        print(jar_name(version, args.loader))
    elif args.action == "games":
        print(json.dumps(target["minecraft_versions"]))
    elif args.action == "notes":
        print(notes(version), end="")
    elif args.action == "stage":
        if not args.loader or not args.build_dir:
            parser.error("stage requires --loader and --build-dir")
        source = args.build_dir / jar_name(version, args.loader)
        if not source.is_file():
            raise ValueError(f"Expected runtime artifact not found: {source}")
        args.dist.mkdir(parents=True, exist_ok=True)
        destination = args.dist / source.name
        destination.write_bytes(source.read_bytes())
        print(destination)
    elif args.action == "verify":
        names = [jar_name(version, loader) for loader in target["loaders"]]
        actual = sorted(p.name for p in args.dist.glob("*.jar"))
        if actual != sorted(names):
            raise ValueError(f"Unexpected release assets: expected {sorted(names)}, got {actual}")
        with (args.dist / "SHA256SUMS").open("w", encoding="utf-8") as sums:
            for name in names:
                sums.write(f"{sha256(args.dist / name)}  {name}\n")
        print("Validated both runtime artifacts and wrote SHA256SUMS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Release manifest error: {error}", file=sys.stderr)
        sys.exit(1)
