"""Talk to a classic Anova Precision Cooker (Bluetooth model) over GATT.

The cooker exposes an HM-10 style serial service (FFE0) with one characteristic
(FFE1). Commands are ASCII lines ending in "\\r", written to FFE1; the answer
comes back as a notification on FFE1, also ending in "\\r".

    read temp       -> "23.5"       current water temperature, in the cooker's unit
    read set temp   -> "57.0"       target temperature
    read unit       -> "c" / "f"
    status          -> "running" / "stopped"
    set temp 57.0   -> "57.0"
    start           -> "start"
    stop            -> "stop"

The cooker accepts one connection at a time, so we connect, talk, and
disconnect again to leave room for the phone app.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
RESPONSE_TIMEOUT = 5
FLUSH_DELAY = 0.5
INVALID = "invalid command"


class AnovaError(Exception):
    """The cooker did not answer as expected."""


@dataclass
class AnovaState:
    """One reading of the cooker."""

    current: float
    target: float
    unit: str  # "c" or "f"
    running: bool


class AnovaClient:
    """Connect, run commands, disconnect."""

    def __init__(self, device: BLEDevice) -> None:
        self._device = device
        self._lock = asyncio.Lock()

    def set_device(self, device: BLEDevice) -> None:
        """Use the freshest BLEDevice (it can move between proxies)."""
        self._device = device

    async def read_state(self) -> AnovaState:
        """Read temperature, target, unit and run state in one connection."""
        current, target, unit, status = await self._run(
            "read temp", "read set temp", "read unit", "status"
        )
        try:
            return AnovaState(
                current=float(current),
                target=float(target),
                unit=unit.lower(),
                running=status.lower() == "running",
            )
        except ValueError as err:
            raise AnovaError(
                f"unexpected answers: {current!r} {target!r} {unit!r} {status!r}"
            ) from err

    async def set_target(self, temperature: float) -> None:
        """Set the target temperature, in the cooker's unit."""
        await self._run(f"set temp {temperature:.1f}")

    async def set_running(self, running: bool) -> None:
        """Start or stop the cooker."""
        await self._run("start" if running else "stop")

    async def _run(self, *commands: str) -> list[str]:
        async with self._lock:
            client = await establish_connection(
                BleakClientWithServiceCache, self._device, self._device.address
            )
            lines: asyncio.Queue[str] = asyncio.Queue()
            buffer = bytearray()

            def _on_notify(_sender: object, data: bytearray) -> None:
                buffer.extend(data)
                while b"\r" in buffer:
                    line, _, rest = buffer.partition(b"\r")
                    buffer[:] = rest
                    lines.put_nowait(line.decode(errors="replace").strip())

            try:
                await client.start_notify(CHAR_UUID, _on_notify)
                await self._flush(client, lines)
                return [await self._command(client, lines, cmd) for cmd in commands]
            finally:
                await client.disconnect()

    async def _flush(
        self, client: BleakClientWithServiceCache, lines: asyncio.Queue[str]
    ) -> None:
        """Terminate whatever junk sits in the cooker's input line.

        The serial module passes its own connect/disconnect notices (e.g.
        "OK+LOST") to the cooker as text, so after a quick reconnect the first
        real command arrives glued to them and is rejected as "Invalid Command".
        A bare "\\r" ends that junk line; its answer is thrown away.
        """
        await client.write_gatt_char(CHAR_UUID, b"\r", response=False)
        await asyncio.sleep(FLUSH_DELAY)
        while not lines.empty():
            lines.get_nowait()

    async def _command(
        self,
        client: BleakClientWithServiceCache,
        lines: asyncio.Queue[str],
        command: str,
    ) -> str:
        """Send one command and return its answer, retrying once if rejected."""
        for attempt in range(2):
            await client.write_gatt_char(
                CHAR_UUID, f"{command}\r".encode(), response=False
            )
            try:
                answer = await asyncio.wait_for(lines.get(), RESPONSE_TIMEOUT)
            except TimeoutError as err:
                raise AnovaError(f"no answer to {command!r}") from err
            if answer.lower() != INVALID or attempt:
                return answer
        return answer
