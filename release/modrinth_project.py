#!/usr/bin/env python3
"""Validate a Modrinth project by ID, slug or URL and extract its canonical ID.

The workflow performs the authenticated network request. This helper is
pure/offline for deterministic CI tests and never prints an API token.
"""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

VALID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{1,63}\Z")


def identifier(raw):
    candidate = raw.strip()
    if not VALID.fullmatch(candidate):
        raise ValueError(f"Invalid Modrinth project identifier {candidate!r}")
    return candidate


def slug_from_url(raw):
    parsed = urlparse(raw.strip())
    if (parsed.scheme != "https"
            or parsed.hostname not in ("modrinth.com", "www.modrinth.com")
            or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.port):
        raise ValueError("Modrinth URL must be HTTPS and hosted on modrinth.com")
    parts = parsed.path.rstrip("/").split("/")
    if len(parts) != 3 or parts[1] != "mod":
        raise ValueError("Expected https://modrinth.com/mod/<slug>")
    return identifier(parts[2])


def lookup(project_id="", slug="", url=""):
    # MODRINTH_PROJECT_ID may be either an actual ID or a slug. The
    # GET /v2/project/{id|slug} endpoint supports both.
    value = project_id.strip() or slug.strip()
    if not value and url.strip():
        value = slug_from_url(url)
    if not value:
        raise ValueError("Set MODRINTH_PROJECT_ID, MODRINTH_PROJECT_SLUG or MODRINTH_PROJECT_URL")
    return identifier(value)


def verify(project, expected_source, project_id="", slug="", url=""):
    canonical = identifier(str(project.get("id") or ""))
    actual_slug = identifier(str(project.get("slug") or ""))
    source = str(project.get("source_url") or "").rstrip("/")
    if source.casefold() != expected_source.rstrip("/").casefold():
        raise ValueError(
            f"Modrinth project source_url must be {expected_source!r}; found {source!r}"
        )
    license_info = project.get("license") or {}
    license_id = license_info.get("id") if isinstance(license_info, dict) else None
    if license_id != "Apache-2.0":
        raise ValueError(
            f"Modrinth project license must be Apache-2.0 before publishing; "
            f"found {license_id!r}. Update the project's License setting."
        )
    if project_id.strip() and identifier(project_id) not in (canonical, actual_slug):
        raise ValueError("Configured MODRINTH_PROJECT_ID does not match resolved project")
    if slug.strip() and identifier(slug) != actual_slug:
        raise ValueError("Configured MODRINTH_PROJECT_SLUG does not match resolved project")
    if url.strip() and slug_from_url(url) != actual_slug:
        raise ValueError("Configured MODRINTH_PROJECT_URL does not match resolved project")
    return canonical


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("lookup", "verify"))
    parser.add_argument("--id", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--project-json", type=Path)
    parser.add_argument("--expected-source",
                        default="https://github.com/qwasdf-1/LMFT-recrafted")
    args = parser.parse_args()
    if args.action == "lookup":
        print(lookup(args.id, args.slug, args.url))
    else:
        if not args.project_json:
            parser.error("verify requires --project-json")
        project = json.loads(args.project_json.read_text(encoding="utf-8"))
        print(verify(project, args.expected_source, args.id, args.slug, args.url))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exception:
        print(f"Modrinth project resolution failed: {exception}", file=sys.stderr)
        sys.exit(1)
