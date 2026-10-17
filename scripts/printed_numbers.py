"""Printed numbers that are not the cost circle.

Base link (CR 2.9.1), minimum deck size (CR 2.11.1), and influence limit
(CR 2.12.1) are on identities. Influence cost (CR 2.14.1) is on every other
card that has an influence bar. A missing bar is not a cost of 0 (CR 2.14.2).
"""

from __future__ import annotations


def apply_printed_numbers(card: dict, c: dict) -> None:
    if c.get("type_code") == "identity":
        if c.get("side_code") == "runner" and c.get("base_link") is not None:
            card["link"] = c["base_link"]
        if c.get("minimum_deck_size") is not None:
            card["minimumDeckSize"] = c["minimum_deck_size"]
        if c.get("influence_limit") is not None:
            card["influenceLimit"] = c["influence_limit"]
        return
    if c.get("faction_cost") is not None:
        card["influence"] = c["faction_cost"]
