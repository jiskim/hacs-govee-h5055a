"""Decode Govee H5055A advertisements.

Payload is the manufacturer data for company id 0x0930 (company id stripped),
20 bytes. Layout as observed (differs from the original H5055 that govee-ble
decodes):

    idx  0  1  2  3  4  5  6  7  8  9  10 .. 19
         0b 41 00 01 01 e4 01 00 08 34 ff .. ff

    5      battery, low 7 bits (0xe4 & 0x7f = 100 %)
    6      top 2 bits: probe pair in this packet (0 = 1/2, 1 = 3/4, 2 = 5/6)
           low 6 bits: probes plugged in
    8-9    first probe of the pair, big-endian signed, 1/100 degC, ffff = none

Where the second probe of each pair lives is not known yet; the raw payload is
exposed as a diagnostic sensor so it can be worked out.
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

    temp = data[8:10]
    probe = pair * 2 + 1
    return {
        "battery": data[5] & 0x7F,
        f"probe_{probe}": None
        if temp == NO_PROBE
        else int.from_bytes(temp, "big", signed=True) / 100,
        "raw": data.hex(),
    }
