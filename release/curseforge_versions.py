#!/usr/bin/env python3
"""Resolve CurseForge game version IDs by version *and category*.

CurseForge uses the same display names in multiple categories (e.g. Bukkit
and Minecraft Java). Always consult /api/game/version-types to select a
Minecraft category, rather than picking the first same-named version.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from manifest import config

KNOWN_ENVIRONMENT_IDS = {"client": 9638, "server": 9639}
# CurseForge Minecraft version *categories* are sometimes named only "26.2"
# rather than "Minecraft 26.2". The API is already scoped to Minecraft.
# Do not infer a version from a missing/unknown category ID.
MINECRAFT_TYPE = re.compile(r"^(?:minecraft(?:\s+|-))?(\d+(?:\.\d+)*)(?:\.x)?$", re.I)


def exact_matches(data, needle):
    return [entry for entry in data
            if str(entry.get("name", "")).casefold() == needle.casefold()
            or str(entry.get("slug", "")).casefold() == needle.casefold()]


def find_exact(data, needle, *, optional=False):
    matches = exact_matches(data, needle)
    ids = sorted({row["id"] for row in matches})
    if len(ids) == 1:
        return ids[0]
    if not ids and optional:
        return None
    raise ValueError(f"CurseForge version {needle!r} has {len(ids)} matches: {ids}")


def minecraft_category_score(version_type, mc):
    """Return type specificity if it describes a Minecraft release category.

    CurseForge may label a version family simply "26.2" (as well as
    "Minecraft 26.2"). A 26.1 family covers 26.1.x hotfixes but excludes
    26.2. The most specific matching family wins. Bukkit/Spigot/other
    named categories and unknown gameVersionTypeIDs are not eligible.
    """
    name = str(version_type.get("name") or "").strip()
    if name.casefold() == "minecraft":
        return 0
    match = MINECRAFT_TYPE.fullmatch(name)
    if not match:
        # Only use a slug as fallback when the type name is absent. A
        # non-Minecraft label (e.g. "Bukkit 26.2") is an explicit exclusion.
        slug = str(version_type.get("slug") or "").strip()
        if name or not slug.casefold().startswith("minecraft-"):
            return None
        suffix = slug[len("minecraft-"):].replace("-", ".")
        match = MINECRAFT_TYPE.fullmatch(suffix)
        if not match:
            return None
    family = match.group(1)
    parts = family.removesuffix(".x").split(".")
    target = mc.split(".")
    if target[:len(parts)] != parts:
        return None
    return len(parts)


def minecraft_version_id(data, mc, version_types=None):
    candidates = exact_matches(data, mc)
    if not candidates:
        raise ValueError(f"CurseForge Minecraft version {mc!r} not found")
    if version_types is None:
        # Local unit tests or a manual resolver without the category table.
        if len({v["id"] for v in candidates}) == 1:
            return candidates[0]["id"]
        raise ValueError(
            f"CurseForge Minecraft version {mc!r} is ambiguous; "
            "fetch /api/game/version-types and pass --version-types "
            "(or use a verified CURSEFORGE_GAME_VERSIONS override)."
        )
    if not isinstance(version_types, list):
        raise ValueError("Expected CurseForge /api/game/version-types JSON array")
    types = {v.get("id"): v for v in version_types}
    scored = []
    diagnostics = []
    for candidate in candidates:
        type_id = candidate.get("gameVersionTypeID")
        category = types.get(type_id, {})
        score = minecraft_category_score(category, mc)
        label = category.get("name") or category.get("slug") or "<unknown type>"
        diagnostics.append(f"{candidate['id']} (type {type_id}: {label})")
        if score is not None:
            scored.append((score, candidate["id"]))
    if scored:
        highest = max(score for score, _ in scored)
        winners = sorted({id_ for score, id_ in scored if score == highest})
        if len(winners) == 1:
            return winners[0]
    raise ValueError(
        f"Could not uniquely identify Minecraft release {mc!r} by "
        "CurseForge gameVersionTypeID. Candidates: "
        + ", ".join(diagnostics)
        + ". Set a verified CURSEFORGE_GAME_VERSIONS override only if "
          "the CurseForge category table itself is ambiguous."
    )


def resolve(data, loader, overrides=None, environment="both", version_types=None):
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
            selected.append(minecraft_version_id(data, mc, version_types))
    selected.append(find_exact(data, loader))

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
    parser.add_argument("--version-types", type=Path)
    parser.add_argument("--loader", choices=("fabric", "neoforge"), required=True)
    parser.add_argument("--overrides", default="")
    parser.add_argument("--environment", default="both")
    args = parser.parse_args()
    overrides = json.loads(args.overrides) if args.overrides else {}
    if not isinstance(overrides, dict):
        raise ValueError("CURSEFORGE_GAME_VERSIONS must be a JSON object")
    data = json.loads(args.versions.read_text(encoding="utf-8"))
    types = (json.loads(args.version_types.read_text(encoding="utf-8"))
             if args.version_types else None)
    print(json.dumps(resolve(data, args.loader, overrides, args.environment, types)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"CurseForge version resolution failed: {exc}", file=sys.stderr)
        sys.exit(1)
