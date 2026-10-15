"""Classify a card's printed abilities under Comprehensive Rules 9.3.

The effect tree stays the instructions. Load in the engine copies each record
back onto the hook that rule already evaluates.
"""

from __future__ import annotations

KEEP = {
    "id",
    "title",
    "type",
    "side",
    "wave",
    "nrdbCode",
    "unsupported",
    "subtypes",
    "faction",
    "playCost",
    "installCost",
    "rezCost",
    "trashCost",
    "strength",
    "memoryCost",
    "agendaPoints",
    "advancementRequirement",
    "influence",
    "deckSize",
    "minimumDeckSize",
    "baseLink",
    "uniqueness",
    "abilities",
    "flavor",
    "illustrator",
}

RESTRICTION_FIELDS = {
    "playAdditionalCost": "play",
    "rezAdditionalCost": "rez",
    "scoreAdditionalCost": "score",
    "stealAdditionalCost": "steal",
    "stealAdditionalCostFromProtectingServer": "steal_from_protecting_server",
    "trashAdditionalCost": "trash",
}

EXACT_HOOKS = {
    "afterMandatoryDraw": "after_mandatory_draw",
    "mirrormorphOnThirdDistinctAction": "mirrormorph_on_third_distinct_action",
}


def hook_to_trigger(hook: str) -> str:
    exact = EXACT_HOOKS.get(hook)
    if exact:
        return exact
    rest = hook[2:] if hook.startswith("on") else hook
    out: list[str] = []
    for index, ch in enumerate(rest):
        if ch.isupper() and index:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def is_effect(value: object) -> bool:
    return isinstance(value, dict) and "op" in value


def _paid(ability: dict) -> dict:
    cost = dict(ability.get("cost") or {})
    if "clicks" not in cost and ability.get("clickCost"):
        cost["clicks"] = ability["clickCost"]
    if "credits" not in cost and ability.get("creditCost"):
        cost["credits"] = ability["creditCost"]
    if not cost:
        clicks = ability.get("clickCost")
        credits = ability.get("creditCost")
        if clicks:
            cost["clicks"] = clicks
        elif credits:
            cost["credits"] = credits
        else:
            cost["credits"] = 0
    record: dict = {
        "class": "paid",
        "id": ability.get("id", "paid"),
        "label": ability.get("label", ability.get("id", "Paid ability")),
        "cost": cost,
        "windows": ability.get("windows") or ["click"],
        "instructions": ability["effect"],
    }
    if ability.get("oncePerTurn"):
        record["flag"] = "once_per_turn"
    elif ability.get("requiresThreat") is not None:
        record["flag"] = {"threat": ability["requiresThreat"]}
    skip = {
        "id",
        "label",
        "clickCost",
        "creditCost",
        "cost",
        "windows",
        "effect",
        "oncePerTurn",
        "requiresThreat",
    }
    for key, value in ability.items():
        if key not in skip:
            record[key] = value
    return record


def _subroutine(ability: dict) -> dict:
    record: dict = {
        "class": "subroutine",
        "id": ability.get("id", "sub"),
        "text": ability.get("text", ""),
        "instructions": ability["effect"],
    }
    for key, value in ability.items():
        if key not in {"id", "text", "effect"}:
            record[key] = value
    return record


def classify_card(card: dict) -> dict:
    """Move hooks into `abilities`. Safe to call on a card already classified."""
    if not isinstance(card, dict) or "id" not in card or "abilities" in card:
        return card
    abilities: list[dict] = []
    restrictions: list[dict] = []
    remove: list[str] = []

    for key, value in list(card.items()):
        if key in KEEP:
            continue
        if key == "paidAbilities" and isinstance(value, list):
            abilities.extend(_paid(item) for item in value if isinstance(item, dict) and "effect" in item)
            remove.append(key)
            continue
        if key == "subroutines" and isinstance(value, list):
            abilities.extend(
                _subroutine(item) for item in value if isinstance(item, dict) and "effect" in item
            )
            remove.append(key)
            continue
        if key in RESTRICTION_FIELDS and is_effect(value):
            restrictions.append({"appliesTo": RESTRICTION_FIELDS[key], "effect": value})
            remove.append(key)
            continue
        if is_effect(value):
            if key == "onPlay":
                abilities.append({"class": "play", "instructions": value})
            else:
                abilities.append(
                    {
                        "class": "conditional",
                        "trigger": hook_to_trigger(key),
                        "instructions": value,
                    }
                )
            remove.append(key)
            continue
        abilities.append({"class": "static", "declaration": {"field": key, "value": value}})
        remove.append(key)

    if restrictions:
        play = next((item for item in abilities if item.get("class") == "play"), None)
        host = play or next((item for item in abilities if item.get("class") != "static"), None)
        if host is None:
            host = {"class": "static", "restrictions": restrictions}
            abilities.append(host)
        else:
            host.setdefault("restrictions", []).extend(restrictions)

    for key in remove:
        del card[key]
    if abilities:
        card["abilities"] = abilities
    return card
