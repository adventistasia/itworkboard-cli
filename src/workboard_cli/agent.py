from workboard_cli.errors import WorkboardError
from workboard_cli.normalize import normalize_item
from workboard_cli.output import (
    build_envelope,
    build_summary_envelope,
)
from workboard_cli.queries import (
    filter_blocked,
    filter_by_owner,
    filter_open,
    filter_overdue,
    filter_recently_updated,
)
from workboard_cli.summaries import build_summary

APPROVED_INTENTS = {
    "open_items",
    "overdue_items",
    "blocked_items",
    "items_by_owner",
    "recently_updated_items",
    "manager_summary",
}


def validate_intent(intent):
    if intent not in APPROVED_INTENTS:
        raise WorkboardError(
            "unsupported_intent",
            f"The intent '{intent}' is not approved for agent use.",
            f"Use one of: {', '.join(sorted(APPROVED_INTENTS))}",
        )


def execute_intent(intent, raw_items, config, params=None):
    params = params or {}
    validate_intent(intent)

    if intent == "items_by_owner" and not params.get("owner"):
        raise WorkboardError(
            "validation_error",
            "The 'items_by_owner' intent requires an --owner parameter.",
            "Provide --owner <name> with the owner's display name or email.",
        )

    if intent == "recently_updated_items" and not params.get("days"):
        raise WorkboardError(
            "validation_error",
            "The 'recently_updated_items' intent requires a --days parameter.",
            "Provide --days <number> with the number of days to look back.",
        )

    items = [normalize_item(i, config) for i in raw_items]

    if intent == "open_items":
        result = filter_open(items)
    elif intent == "overdue_items":
        result = filter_overdue(items)
    elif intent == "blocked_items":
        result = filter_blocked(items)
    elif intent == "items_by_owner":
        result = filter_by_owner(items, params["owner"])
    elif intent == "recently_updated_items":
        result = filter_recently_updated(items, params["days"])
    elif intent == "manager_summary":
        summary = build_summary(items)
        return build_summary_envelope(summary, config)
    else:
        raise WorkboardError("unsupported_intent", f"Intent '{intent}' not implemented.")

    return build_envelope(result, intent, config, filters=params)
