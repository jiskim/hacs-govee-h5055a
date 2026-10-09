"""Decode Govee H5055A advertisements.

Payload is the manufacturer data for company id 0x0930 (company id stripped),
20 bytes. Layout as observed (differs from the original H5055 that govee-ble
decodes):

    idx  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19
         0b 41 00 01 01 e4 49 00 ff ff ff ff ff ff 08 34 ff ff ff ff

    5      battery, low 7 bits (0xe4 & 0x7f = 100 %)
    6      top 2 bits: probe pair in this packet (0 = 1/2, 1 = 3/4, 2 = 5/6)
           low 6 bits: probes plugged in (bit 0 = probe 1 .. bit 5 = probe 6)
    8-9    first probe of the pair, big-endian signed, 1/100 degC, ffff = none
    14-15  second probe of the pair, same encoding
    10-13, 16-19  not decoded (probably alarm set points)
"""

from __future__ import annotations

PAYLOAD_LEN = 20
NO_PROBE = b"\xff\xff"


def parse(data: bytes) -> dict[str, float | int | str | None] | None:
    """Return the values carried by one advertisement, or None if not ours."""
    if len(data) < PAYLOAD_LEN:
        return None
    pair = data[6] >> 6
    if pair > 2:
        return None

    first = pair * 2 + 1
    return {
        "battery": data[5] & 0x7F,
        f"probe_{first}": _temp(data[8:10]),
        f"probe_{first + 1}": _temp(data[14:16]),
        "raw": data.hex(),
    }


def _temp(raw: bytes) -> float | None:
    if raw == NO_PROBE:
        return None
    return int.from_bytes(raw, "big", signed=True) / 100
