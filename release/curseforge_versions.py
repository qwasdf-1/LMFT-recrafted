#!/usr/bin/env python3
"""Resolve CurseForge numeric game-version tags for universal LMFT artifacts.

Usage: python3 release/curseforge_versions.py --versions /tmp/versions.json
       --loader fabric --overrides "$CURSEFORGE_GAME_VERSIONS"
The JSON output is a single list of version IDs (Minecraft + loader +
optional Java 25 + environment), suitable for /api/projects/:id/upload-file.
"""
import argparse
import json
from pathlib import Path
import sys

from manifest import config

KNOWN_ENVIRONMENT_IDS = {"client": 9638, "server": 9639}


def find_exact(data, needle, *, optional=False):
    options = [v["id"] for v in data if
               str(v.get("name", "")).casefold() == needle.casefold()
               or str(v.get("slug", "")).casefold() == needle.casefold()]
    options = sorted(set(options))
    if len(options) == 1:
        return options[0]
    if not options and optional:
        return None
    raise ValueError(
        f"CurseForge game version {needle!r} yielded {len(options)} IDs: {options}. "
        "Use explicit CURSEFORGE_GAME_VERSIONS overrides for Minecraft versions."
    )


def resolve(data, loader, overrides=None, environment="both"):
    _version, release = config()
    if loader not in release["loaders"]:
        raise ValueError("Unsupported loader " + loader)
    if not isinstance(data, list):
        raise ValueError("Expected CurseForge /api/game/versions JSON array")
    overrides = overrides or {}
    selected = []
    for mc in release["minecraft_versions"]:
        if mc in overrides:
            candidate = overrides[mc]
            if isinstance(candidate, int):
                candidate = [candidate]
            if not isinstance(candidate, list) or not candidate or not all(
                isinstance(x, int) and x > 0 for x in candidate
            ):
                raise ValueError(f"Invalid numeric CurseForge override for {mc}")
            selected.extend(candidate)
        else:
            selected.append(find_exact(data, mc))
    selected.append(find_exact(data, loader))

    # CurseForge may not expose Java-version tags in all environments.
    java = find_exact(data, "Java 25", optional=True)
    if java:
        selected.append(java)
    envs = ["client", "server"] if environment == "both" else [environment]
    if any(x not in ("client", "server") for x in envs):
        raise ValueError("CURSEFORGE_ENVIRONMENT must be client, server or both")
    for env in envs:
        selected.append(find_exact(data, env, optional=True)
                        or KNOWN_ENVIRONMENT_IDS[env])
    return sorted(set(selected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--versions", type=Path, required=True)
    parser.add_argument("--loader", choices=("fabric", "neoforge"), required=True)
    parser.add_argument("--overrides", default="")
    parser.add_argument("--environment", default="both")
    args = parser.parse_args()
    overrides = json.loads(args.overrides) if args.overrides else {}
    if not isinstance(overrides, dict):
        raise ValueError("CURSEFORGE_GAME_VERSIONS must be a JSON object")
    data = json.loads(args.versions.read_text(encoding="utf-8"))
    print(json.dumps(resolve(data, args.loader, overrides, args.environment)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"CurseForge version resolution failed: {exc}", file=sys.stderr)
        sys.exit(1)
