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
            raise AnovaError(f"unexpected answer: {current!r} {target!r}") from err

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
            try:
                return [await self._command(client, cmd) for cmd in commands]
            finally:
                await client.disconnect()

    async def _command(self, client: BleakClientWithServiceCache, command: str) -> str:
        buffer = bytearray()
        done = asyncio.Event()

        def _on_notify(_sender: object, data: bytearray) -> None:
            buffer.extend(data)
            if b"\r" in buffer:
                done.set()

        await client.start_notify(CHAR_UUID, _on_notify)
        try:
            await client.write_gatt_char(CHAR_UUID, f"{command}\r".encode(), response=False)
            await asyncio.wait_for(done.wait(), RESPONSE_TIMEOUT)
        except TimeoutError as err:
            raise AnovaError(f"no answer to {command!r}") from err
        finally:
            await client.stop_notify(CHAR_UUID)
        return buffer.split(b"\r", 1)[0].decode(errors="replace").strip()
