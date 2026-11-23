#!/usr/bin/env python3
"""Integration test: real Minecraft player connections receive LMFT chat warnings.

CI-only dependency: ProtoBot (pinned by workflow). No mod or server code is
changed by the probe. Two offline players stay connected for reload tests.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time

from protobot import Bot
from server_integration import Rcon, await_condition, count_warnings, member_matches, rewrite_tag

TAG = "lmft_test:recovery"
REQUIRED_TAGS = ("lmft_test:recovery", "lmft_test:missing_tag_reference")
WARN_PREFIX = "Load My F***ing Tags"
OP_NAME = "LmftOp"
USER_NAME = "LmftGuest"


def is_lmft_notice(component) -> bool:
    raw = json.dumps(component, ensure_ascii=False, default=str)
    return WARN_PREFIX in raw or "lmft.cooked_tags_message" in raw


class Client:
    def __init__(self, name: str, version: str, loader: str):
        # The mod is server-side; no client-side LMFT installation is required.
        self.bot = Bot("127.0.0.1", username=name, version=version,
                       resolve_srv=False, loader=loader)
        self.name = name
        self.warnings: list[str] = []
        self.other_messages: list[str] = []

        @self.bot.on("system_chat")
        async def on_chat(component, overlay):
            message = json.dumps(component, ensure_ascii=False, default=str)
            if is_lmft_notice(component):
                self.warnings.append(message)
                print(f"LMFT notice to {self.name}: {message[:260]}", flush=True)
            else:
                self.other_messages.append(message)

        @self.bot.on("error")
        async def on_error(error):
            print(f"Client {self.name}: {type(error).__name__}: {error}", flush=True)

    async def connect(self):
        await self.bot.start()
        await self.bot.wait_ready(timeout=35)
        await self.bot.wait_loaded(timeout=35)
        await asyncio.sleep(1.0)
        if self.bot.closed.is_set():
            raise AssertionError(f"{self.name} disconnected: {self.bot.disconnect_reason}")
        print(f"Client {self.name} joined, notices={len(self.warnings)}", flush=True)

    async def close(self):
        await self.bot.close()


def expected(mode: str, operator: bool) -> bool:
    if mode == "public":
        return True
    return mode == "operator-only" and operator


def assert_delta(client: Client, initial_count: int, should_warn: bool, label: str):
    delta = len(client.warnings) - initial_count
    if delta != int(should_warn):
        raise AssertionError(
            f"{label}: {client.name} expected {int(should_warn)} LMFT warnings, "
            f"received {delta}; total={len(client.warnings)}, "
            f"messages={client.warnings}"
        )
    print(f"PASS: {label}: {client.name} delta={delta}", flush=True)


async def broken_reload(rcon: Rcon, clients: list[tuple[Client, bool]],
                        mode: str, log_file: Path, label: str):
    counts = {tag: count_warnings(log_file, tag) for tag in REQUIRED_TAGS}
    before = [(client, role, len(client.warnings)) for client, role in clients]
    print(f"Triggering broken reload: {label}", flush=True)
    rcon.command("reload")
    await asyncio.to_thread(await_condition, "broken reload tag callbacks",
        lambda: all(count_warnings(log_file, tag) > counts[tag] for tag in REQUIRED_TAGS),
        65.0)
    # Give PlayerList.reloadResources callback and client packet delivery time.
    await asyncio.sleep(3.0)
    for client, op, count in before:
        assert_delta(client, count, expected(mode, op), label)


async def clean_reload(rcon: Rcon, clients: list[tuple[Client, bool]],
                       pack: Path, log_file: Path):
    counts = {tag: count_warnings(log_file, tag) for tag in REQUIRED_TAGS}
    before = [(client, len(client.warnings)) for client, _ in clients]
    rewrite_tag(pack, "recovery", ["minecraft:dirt"])
    rewrite_tag(pack, "missing_tag_reference", ["minecraft:stone"])
    print("Triggering clean reload", flush=True)
    rcon.command("reload")
    await asyncio.to_thread(await_condition, "clean tag membership applied",
        lambda: member_matches(rcon, TAG, "dirt"), 65.0)
    await asyncio.sleep(3.0)
    for client, count in before:
        assert_delta(client, count, False, "clean reload")
    for tag in REQUIRED_TAGS:
        if count_warnings(log_file, tag) != counts[tag]:
            raise AssertionError(f"Clean reload still logged broken tag {tag}")
    print("PASS: clean reload suppressed LMFT chat", flush=True)


async def verify(mode: str, version: str, loader: str, pack: Path, log_file: Path):
    rcon = None
    all_clients = []
    try:
        await asyncio.to_thread(await_condition, "server ready",
            lambda: log_file.exists()
            and "Done (" in log_file.read_text(encoding="utf8", errors="replace"),
            180.0)
        def get_rcon():
            nonlocal rcon
            rcon = Rcon()
            return True
        await asyncio.to_thread(await_condition, "RCON listener", get_rcon, 35.0)
        if not all(count_warnings(log_file, tag) >= 1 for tag in REQUIRED_TAGS):
            raise AssertionError("Test pack did not produce LMFT recovery logs")

        # New nonoperator connection. Register packet listener *before* logging in.
        guest = Client(USER_NAME, version, loader)
        all_clients.append(guest)
        await guest.connect()
        assert_delta(guest, 0, expected(mode, False), "guest initial login")

        # First operator login seeds a valid offline-mode profile for /op. It
        # is initially nonoperator, then reconnects after being granted OP.
        seed = Client(OP_NAME, version, loader)
        all_clients.append(seed)
        await seed.connect()
        assert_delta(seed, 0, expected(mode, False), "operator profile seed")
        result = rcon.command(f"op {OP_NAME}")
        print(f"/op response: {result}", flush=True)
        await seed.close()
        await asyncio.sleep(1.0)
        op = Client(OP_NAME, version, loader)
        all_clients.append(op)
        await op.connect()
        assert_delta(op, 0, expected(mode, True), "operator login after /op")
        clients = [(guest, False), (op, True)]

        # Broken reload sends to eligible connected players, exactly once.
        await broken_reload(rcon, clients, mode, log_file, "first broken /reload")

        # Clean reload should clear warning state and notify nobody.
        await clean_reload(rcon, clients, pack, log_file)

        # A subsequent broken reload must reactivate warning delivery.
        rewrite_tag(pack, "recovery", ["minecraft:stone", "lmft_test:missing_block"])
        rewrite_tag(pack, "missing_tag_reference", [
            "minecraft:stone", "#lmft_test:not_a_tag"
        ])
        await broken_reload(rcon, clients, mode, log_file, "reintroduced broken /reload")

        # Inactive interval must not generate duplicate warnings.
        totals = [len(client.warnings) for client, _ in clients]
        await asyncio.sleep(2.0)
        if totals != [len(client.warnings) for client, _ in clients]:
            raise AssertionError("Unsolicited duplicate LMFT warnings")
        print(f"PASS multiplayer notification mode={mode}, loader={loader}", flush=True)
        rcon.command("stop")
    finally:
        for client in reversed(all_clients):
            try:
                await client.close()
            except Exception:
                pass
        if rcon is not None:
            rcon.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("public", "operator-only", "disabled", "jvm-disabled"), required=True)
    parser.add_argument("--version", default="26.3")
    parser.add_argument("--loader", choices=("fabric", "neoforge"), required=True)
    parser.add_argument("--server-log", type=Path, required=True)
    parser.add_argument("--datapack", type=Path, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(verify(args.mode, args.version, args.loader,
                           args.datapack, args.server_log))
    except BaseException as exc:
        print(f"FAIL multiplayer: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
