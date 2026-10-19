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
    "influenceLimit",
    "deckLimit",
    "deckSize",
    "minimumDeckSize",
    "baseLink",
    "link",
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
    return annotate_card(card)


CLASS_RULE = {
    "static": "9.3.7a",
    "paid": "9.3.7b",
    "conditional": "9.3.7c",
    "play": "9.3.7d",
    "subroutine": "9.3.7e",
}

FLAG_RULE = {
    "access": "9.3.6b",
    "interface": "9.3.6c",
    "interrupt": "9.3.6d",
    "persistent": "9.3.6e",
    "once_per_turn": "9.3.6g",
}

# Engine fields that implement a printed access ability (CR 9.3.6b).
ACCESS_FIELDS = {
    "accessTrashFree",
    "accessTrashFromGrip",
    "accessTrashSelfNonAgendaThenDraw",
    "onAccessTrashGain",
    "accessTrashWithVirus",
    "accessTrashPayingPrintedCostFromStealth",
    "accessHostNonAgendaFaceup",
    "accessTrashNonAgendaWithVirusEqualPrintedCost",
}

# The persistent flag sits on the printed ability, not on its own declaration.
# CR 9.3.6e / 9.12.5.
PERSISTENT_ON = {
    "red-herrings": lambda ability: _field(ability) == "stealAdditionalCreditsFromProtectingServer",
    "ben-musashi": lambda ability: bool(ability.get("restrictions")),
    "mahkota-langit-grid": lambda ability: _field(ability) == "serverRootAssetTrashCostBonus",
    "tucana": lambda ability: ability.get("trigger") == "agenda_scored_or_stolen",
    "daniela-jorge-inacio": lambda ability: bool(ability.get("restrictions")),
    "overseer-matrix": lambda ability: (
        _field(ability) == "mayPayCreditsToTagWhenRunnerTrashesFromThisServerOrRoot"
    ),
    "old-hollywood-grid": lambda ability: _field(ability) == "cannotStealUnlessCopyInRunnerScore",
}


def _field(ability: dict) -> str | None:
    declaration = ability.get("declaration")
    if isinstance(declaration, dict):
        field = declaration.get("field")
        if isinstance(field, str):
            return field
    return None


def _flag_items(flag: object) -> list[object]:
    if flag is None:
        return []
    if isinstance(flag, list):
        return list(flag)
    return [flag]


def _has_flag(ability: dict, word: str) -> bool:
    return any(item == word for item in _flag_items(ability.get("flag")))


def _add_flag(ability: dict, word: str) -> None:
    if _has_flag(ability, word):
        return
    items = _flag_items(ability.get("flag"))
    items.insert(0, word)
    ability["flag"] = items[0] if len(items) == 1 else items


def _mentions_access(value: object) -> bool:
    if isinstance(value, dict):
        if any(key in ACCESS_FIELDS for key in value):
            return True
        return any(_mentions_access(child) for child in value.values())
    if isinstance(value, list):
        return any(_mentions_access(child) for child in value)
    return False


def _is_access(ability: dict) -> bool:
    if _field(ability) in ACCESS_FIELDS:
        return True
    declaration = ability.get("declaration")
    if isinstance(declaration, dict):
        return _mentions_access(declaration.get("value"))
    return False


def _is_icebreaker(card: dict) -> bool:
    if "icebreaker" in (card.get("subtypes") or []):
        return True
    return any(_field(ability) == "breaker" for ability in card.get("abilities") or [])


def _collect_kinds(node: object, found: list[str]) -> None:
    if isinstance(node, dict):
        kind = node.get("kind")
        if isinstance(kind, str):
            found.append(kind)
        for child in node.values():
            _collect_kinds(child, found)
    elif isinstance(node, list):
        for child in node:
            _collect_kinds(child, found)


def _is_interface(card: dict, ability: dict) -> bool:
    """Interface is the break or pump ability (CR 9.3.6c), not every encounter ability."""
    if not _is_icebreaker(card):
        return False
    if _field(ability) == "breaker":
        return True
    if ability.get("class") != "paid" or ability.get("windows") != ["encounter_paw"]:
        return False
    kinds: list[str] = []
    _collect_kinds(ability.get("instructions"), kinds)
    blob = f"{ability.get('label') or ''} {' '.join(kinds)}".lower()
    return any(word in blob for word in ("break", "pump", "strength"))


def _remove_flag(ability: dict, word: str) -> None:
    items = [item for item in _flag_items(ability.get("flag")) if item != word]
    if not items:
        ability.pop("flag", None)
        return
    ability["flag"] = items[0] if len(items) == 1 else items


def _is_interrupt(ability: dict) -> bool:
    windows = ability.get("windows") or []
    return bool(windows) and all(
        isinstance(window, str) and window.endswith("_interrupt") for window in windows
    )


def _is_persistent_declaration(ability: dict) -> bool:
    declaration = ability.get("declaration")
    return (
        isinstance(declaration, dict)
        and declaration.get("field") == "persistent"
        and declaration.get("value") is True
    )


def _effect_hooks(value: dict) -> list[tuple[str, dict]]:
    if "op" in value:
        return []
    return [
        (key, child)
        for key, child in value.items()
        if key.startswith("on") and isinstance(child, dict) and "op" in child
    ]


def _lift_hosted(abilities: list[dict]) -> list[dict]:
    """A hook stored inside a declaration or a paid run becomes its own ability."""
    lifted: list[dict] = []
    for ability in abilities:
        lifted.append(ability)
        declaration = ability.get("declaration")
        if isinstance(declaration, dict) and isinstance(declaration.get("value"), dict):
            value = declaration["value"]
            for key, child in _effect_hooks(value):
                del value[key]
                lifted.append(
                    {
                        "class": "conditional",
                        "trigger": hook_to_trigger(key),
                        "host": declaration["field"],
                        "instructions": child,
                    }
                )
        starts = ability.get("startsRun")
        if ability.get("class") == "paid" and isinstance(starts, dict):
            hooks = _effect_hooks(starts)
            if not hooks:
                continue
            paid_id = ability.get("id")
            if not isinstance(paid_id, str) or not paid_id:
                raise ValueError("a paid run follow-up needs an ability id")
            for key, child in hooks:
                del starts[key]
                lifted.append(
                    {
                        "class": "conditional",
                        "trigger": hook_to_trigger(key),
                        "host": "startsRun",
                        "hostAbility": paid_id,
                        "instructions": child,
                    }
                )
    return lifted


def _stamp(ability: dict) -> dict:
    rule = CLASS_RULE[ability["class"]]
    flag_rules: list[str] = []
    for item in _flag_items(ability.get("flag")):
        if isinstance(item, str):
            flag_rules.append(FLAG_RULE[item])
        elif isinstance(item, dict) and "threat" in item:
            flag_rules.append("9.3.6f")
    stamped: dict = {"class": ability["class"], "rule": rule}
    if len(flag_rules) == 1:
        stamped["flagRule"] = flag_rules[0]
    elif flag_rules:
        stamped["flagRule"] = flag_rules
    if "flag" in ability:
        stamped["flag"] = ability["flag"]
    for key, value in ability.items():
        if key in {"class", "rule", "flagRule", "flag"}:
            continue
        stamped[key] = value
    return stamped


def annotate_card(card: dict) -> dict:
    """Record CR 9.3.6 flags and 9.3.7 rule numbers. Safe to run again."""
    abilities = card.get("abilities")
    if not isinstance(abilities, list):
        return card
    abilities = _lift_hosted([item for item in abilities if isinstance(item, dict)])
    persistent = PERSISTENT_ON.get(card.get("id"))
    if persistent is not None and any(_is_persistent_declaration(item) for item in abilities):
        kept: list[dict] = []
        matched = False
        for ability in abilities:
            if _is_persistent_declaration(ability):
                continue
            if persistent(ability):
                _add_flag(ability, "persistent")
                matched = True
            kept.append(ability)
        if not matched:
            raise ValueError(f"{card.get('id')}: persistent flag did not land on an ability")
        abilities = kept
    elif any(_is_persistent_declaration(item) for item in abilities):
        raise ValueError(f"{card.get('id')}: persistent declaration has no printed ability")
    icebreaker = _is_icebreaker(card)
    for ability in abilities:
        if _is_access(ability):
            _add_flag(ability, "access")
        if icebreaker and _is_interface(card, ability):
            _add_flag(ability, "interface")
        elif ability.get("class") == "paid" and _has_flag(ability, "interface"):
            _remove_flag(ability, "interface")
        if _is_interrupt(ability):
            _add_flag(ability, "interrupt")
    card["abilities"] = [_stamp(ability) for ability in abilities]
    return card
