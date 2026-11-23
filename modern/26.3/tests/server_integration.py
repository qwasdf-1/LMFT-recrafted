#!/usr/bin/env python3
"""End-to-end Minecraft dedicated-server tag and reload checks via local RCON.

Uses Python's standard library. The test server must be ephemeral, offline,
RCON-enabled, and have the fixture datapack installed before first startup.
"""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys
import time

PASSWORD = "lmft_ci_only"
RCON_PORT = 25575
TAG1 = "lmft_test:recovery"
TAG2 = "lmft_test:missing_tag_reference"
OPTIONAL = "lmft_test:optional"
REMOVAL = "lmft_test:neoforge_removal"
TEST_POS = "0 96 0"


def read_exact(sock: socket.socket, count: int) -> bytes:
    result = bytearray()
    while len(result) < count:
        data = sock.recv(count - len(result))
        if not data:
            raise ConnectionError("RCON socket closed unexpectedly")
        result.extend(data)
    return bytes(result)


def read_packet(sock: socket.socket) -> tuple[int, int, str]:
    (length,) = struct.unpack("<i", read_exact(sock, 4))
    if not 10 <= length <= 4096:
        raise ConnectionError(f"Invalid RCON packet size {length}")
    data = read_exact(sock, length)
    request_id, packet_type = struct.unpack("<ii", data[:8])
    return request_id, packet_type, data[8:-2].decode("utf-8", errors="replace")


def send_packet(sock: socket.socket, request_id: int, packet_type: int, payload: str) -> None:
    encoded = payload.encode("utf-8") + b"\x00\x00"
    body = struct.pack("<ii", request_id, packet_type) + encoded
    sock.sendall(struct.pack("<i", len(body)) + body)


class Rcon:
    def __init__(self, host: str = "127.0.0.1", port: int = RCON_PORT):
        self.sock = socket.create_connection((host, port), timeout=6)
        self.sock.settimeout(6)
        send_packet(self.sock, 41, 3, PASSWORD)
        for _ in range(3):
            ident, kind, _text = read_packet(self.sock)
            if ident == -1:
                raise AssertionError("RCON authentication rejected")
            if ident == 41 and kind == 2:
                break
        else:
            raise AssertionError("RCON authentication response missing")
        self.next_id = 100

    def command(self, text: str) -> str:
        self.next_id += 1
        ident = self.next_id
        send_packet(self.sock, ident, 2, text)
        for _ in range(3):
            reply_id, _kind, response = read_packet(self.sock)
            if reply_id == ident:
                return response
        raise AssertionError(f"No RCON response for {text!r}")

    def close(self) -> None:
        self.sock.close()


def await_condition(description: str, check, timeout: float = 90.0):
    deadline = time.monotonic() + timeout
    last_exception = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (OSError, ConnectionError, TimeoutError) as exception:
            last_exception = exception
        time.sleep(1.0)
    raise AssertionError(f"Timed out waiting for {description}; last error={last_exception}")


def count_warnings(log_file: Path, tag: str) -> int:
    if not log_file.exists():
        return 0
    return log_file.read_text(encoding="utf-8", errors="replace").count(
        f"Couldn't load certain entries within tag {tag}:"
    )


def rewrite_tag(root: Path, name: str, values: list[str]) -> None:
    path = root / "data" / "lmft_test" / "tags" / "block" / (name + ".json")
    path.write_text(json.dumps({"values": values}, indent=2) + "\n", encoding="utf-8")


def member_matches(rcon: Rcon, tag: str, block: str) -> bool:
    rcon.command(f"setblock {TEST_POS} minecraft:{block}")
    rcon.command("scoreboard players set probe lmft_probe 0")
    rcon.command(
        f"execute if block {TEST_POS} #{tag} run scoreboard players set probe lmft_probe 1"
    )
    output = rcon.command("scoreboard players get probe lmft_probe")
    # Unlike /say, scoreboard readback must produce a numeric response.
    # Assert the exact value, not the success of the preceding command.
    import re
    match = re.search(r"(?<![0-9])([01])(?![0-9])", output)
    if match is None:
        raise AssertionError(f"No numeric scoreboard readback for #{tag}: {output!r}")
    result = match.group(1) == "1"
    print(f"probe: minecraft:{block} in #{tag}: {result}", flush=True)
    return result


def assert_member(rcon: Rcon, tag: str, block: str, should_match: bool) -> None:
    found = member_matches(rcon, tag, block)
    if found != should_match:
        raise AssertionError(
            f"Expected {block} in #{tag} to be {should_match}; got {found}"
        )


def assert_membership(rcon: Rcon, loader: str, clean: bool) -> None:
    # A clean reload deliberately changes the recovery tag's *resolved* value
    # to dirt, so membership establishes that tag reload actually finished.
    assert_member(rcon, TAG1, "dirt" if clean else "stone", True)
    assert_member(rcon, TAG1, "stone" if clean else "dirt", False)
    assert_member(rcon, TAG2, "stone", True)
    assert_member(rcon, OPTIONAL, "stone", True)
    if loader == "neoforge":
        # NeoForge supports per-tag remove entries; Fabric intentionally ignores them.
        assert_member(rcon, REMOVAL, "dirt", True)
        assert_member(rcon, REMOVAL, "stone", False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-log", type=Path, required=True)
    parser.add_argument("--datapack", type=Path, required=True)
    parser.add_argument("--loader", choices=("fabric", "neoforge"), required=True)
    args = parser.parse_args()

    root = args.datapack
    rcon = None
    try:
        # Server startup should resolve two broken required entries, while the
        # absent optional tag entry (and absent optional NeoForge removal) are safe.
        await_condition("server ready", lambda: args.server_log.exists()
            and "Done (" in args.server_log.read_text(errors="replace"), timeout=180)
        def connect():
            nonlocal rcon
            rcon = Rcon()
            return True
        await_condition("RCON authentication", connect, timeout=25)
        print("RCON authenticated", flush=True)
        rcon.command("forceload add 0 0")
        rcon.command("scoreboard objectives add lmft_probe dummy")
        assert_membership(rcon, args.loader, clean=False)

        for tag in (TAG1, TAG2):
            if count_warnings(args.server_log, tag) < 1:
                raise AssertionError(f"Initial recovery warning for {tag} missing")
        if count_warnings(args.server_log, OPTIONAL) > 0:
            raise AssertionError("Optional missing tag was incorrectly treated as required")
        if count_warnings(args.server_log, REMOVAL) > 0:
            raise AssertionError("NeoForge optional removal unexpectedly reported invalid")
        print("Initial recovered tag membership and optional semantics passed", flush=True)

        # A second reload while still broken must recover again, with correct IDs.
        rcon.command("reload")
        await_condition("second broken tag load",
            lambda: all(count_warnings(args.server_log, tag) >= 2
                        for tag in (TAG1, TAG2)), timeout=90)
        assert_membership(rcon, args.loader, clean=False)
        print("Broken-tag /reload recovered again", flush=True)

        before_clean = {tag: count_warnings(args.server_log, tag) for tag in (TAG1, TAG2)}
        # Switch one valid tag to dirt and eliminate all missing *required*
        # references. Its changed contents provide the reload-complete signal.
        rewrite_tag(root, "recovery", ["minecraft:dirt"])
        rewrite_tag(root, "missing_tag_reference", ["minecraft:stone"])
        rcon.command("reload")
        await_condition("clean tag contents after reload",
            lambda: member_matches(rcon, TAG1, "dirt"), timeout=90)
        assert_membership(rcon, args.loader, clean=True)
        if any(count_warnings(args.server_log, tag) != before_clean[tag] for tag in (TAG1, TAG2)):
            raise AssertionError("Clean reload emitted an invalid-entry warning")
        print("Clean /reload replaced tag values and produced no warnings", flush=True)

        # Return to broken input; this tests re-enabling the recovery path after
        # successful clean loading rather than relying on startup-only behavior.
        rewrite_tag(root, "recovery", ["minecraft:stone", "lmft_test:missing_block"])
        rewrite_tag(root, "missing_tag_reference",
                    ["minecraft:stone", "#lmft_test:not_a_tag"])
        rcon.command("reload")
        await_condition("recovered tag after clean reload",
            lambda: all(count_warnings(args.server_log, tag) > before_clean[tag]
                        for tag in (TAG1, TAG2)), timeout=90)
        assert_membership(rcon, args.loader, clean=False)
        print(f"PASS: {args.loader} membership, NeoForge removals, repeated reloads", flush=True)
        rcon.command("stop")
        return 0
    except Exception as exception:
        print(f"FAIL: {exception}", file=sys.stderr, flush=True)
        if rcon is not None:
            try:
                rcon.command("stop")
            except Exception:
                pass
        return 1
    finally:
        if rcon is not None:
            rcon.close()


if __name__ == "__main__":
    sys.exit(main())
