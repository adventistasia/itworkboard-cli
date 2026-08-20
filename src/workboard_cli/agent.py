from workboard_cli.errors import WorkboardError
from workboard_cli.normalize import normalize_item
from workboard_cli.output import (
    build_envelope,
    build_summary_envelope,
)
from workboard_cli.queries import (
    compute_cycle_time_stats,
    filter_blocked,
    filter_by_decision_authority,
    filter_by_owner,
    filter_by_project,
    filter_by_stage,
    filter_new_items,
    filter_open,
    filter_overdue,
    filter_recently_completed,
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
    "new_items",
    "recently_completed_items",
    "cycle_time_stats",
    "items_by_project",
    "items_by_stage",
    "items_by_decision_authority",
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

    if intent == "new_items" and not params.get("days"):
        raise WorkboardError(
            "validation_error",
            "The 'new_items' intent requires a --days parameter.",
            "Provide --days <number> with the number of days to look back.",
        )

    if intent == "recently_completed_items" and not params.get("days"):
        raise WorkboardError(
            "validation_error",
            "The 'recently_completed_items' intent requires a --days parameter.",
            "Provide --days <number> with the number of days to look back.",
        )

    if intent == "cycle_time_stats":
        group_by = params.get("group_by", "owner")
        if group_by not in ("owner", "stage"):
            raise WorkboardError(
                "validation_error",
                "The 'cycle_time_stats' intent requires --group-by to be 'owner' or 'stage'.",
                "Provide --group-by owner or --group-by stage.",
            )

    if intent == "items_by_project" and not params.get("project"):
        raise WorkboardError(
            "validation_error",
            "The 'items_by_project' intent requires a --project parameter.",
            "Provide --project <name> with the project name.",
        )

    if intent == "items_by_stage" and not params.get("stage"):
        raise WorkboardError(
            "validation_error",
            "The 'items_by_stage' intent requires a --stage parameter.",
            "Provide --stage <name> with the stage name.",
        )

    if intent == "items_by_decision_authority" and not params.get("person"):
        raise WorkboardError(
            "validation_error",
            "The 'items_by_decision_authority' intent requires a --person parameter.",
            "Provide --person <name> with the decision authority's display name.",
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
    elif intent == "new_items":
        result = filter_new_items(items, params["days"])
    elif intent == "recently_completed_items":
        result = filter_recently_completed(items, params["days"])
    elif intent == "items_by_project":
        result = filter_by_project(items, params["project"])
    elif intent == "items_by_stage":
        result = filter_by_stage(items, params["stage"])
    elif intent == "items_by_decision_authority":
        result = filter_by_decision_authority(items, params["person"])
    elif intent == "cycle_time_stats":
        group_by = params.get("group_by", "owner")
        stats = compute_cycle_time_stats(items, group_by)
        return build_summary_envelope(
            stats, config, intent_name="cycle_time_stats", filters={"group_by": group_by}
        )
    elif intent == "manager_summary":
        summary = build_summary(items)
        return build_summary_envelope(summary, config, intent_name="manager_summary")
    else:
        raise WorkboardError("unsupported_intent", f"Intent '{intent}' not implemented.")

    return build_envelope(result, intent, config, filters=params)
