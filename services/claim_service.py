from __future__ import annotations

from typing import Optional

from database.database import get_connection
from database.queries import (
    create_claim,
    get_claim,
    get_claim_by_pair,
    get_item,
    update_claim,
    update_item_status,
    update_match_status,
)


def _is_claim_blocked(lost_item_id: int, found_item_id: int) -> bool:
    lost = get_item(lost_item_id)
    found = get_item(found_item_id)
    if not lost or not found:
        return True
    if lost.get("status") == "resolved" or found.get("status") == "resolved":
        return True
    existing = get_claim_by_pair(lost_item_id, found_item_id)
    return existing is not None and existing.get("status") in {"potential", "approved", "resolved"}


def create_claim_for_match(
    lost_item_id: int,
    found_item_id: int,
    requested_by_user_id: int,
    notes: Optional[str] = None,
) -> Optional[int]:
    """Create a claim only when the item pair is still open and unclaimed."""
    if _is_claim_blocked(lost_item_id, found_item_id):
        return None
    claim_id = create_claim(lost_item_id, found_item_id, requested_by_user_id, notes)
    if claim_id:
        update_claim(claim_id, status="potential", verification_status="pending", handover_status="pending")
    return claim_id


def approve_claim(
    claim_id: int,
    reviewed_by_user_id: int,
    notes: Optional[str] = None,
) -> bool:
    claim = get_claim(claim_id)
    if not claim or claim.get("status") == "resolved":
        return False
    update_claim(
        claim_id,
        status="approved",
        verification_status="approved",
        handover_status="pending",
        notes=notes,
        reviewed_by_user_id=reviewed_by_user_id,
    )
    return True


def resolve_claim_handover(
    claim_id: int,
    reviewed_by_user_id: int,
    notes: Optional[str] = None,
) -> bool:
    claim = get_claim(claim_id)
    if not claim or claim.get("status") == "resolved":
        return False

    lost_item_id = int(claim["lost_item_id"])
    found_item_id = int(claim["found_item_id"])

    update_claim(
        claim_id,
        status="resolved",
        verification_status="approved",
        handover_status="handed_over",
        notes=notes,
        reviewed_by_user_id=reviewed_by_user_id,
    )
    update_item_status(lost_item_id, "resolved")
    update_item_status(found_item_id, "resolved")

    # Keep the history and the item relationships intact, while removing active listings.
    # Match entries are kept for auditing and future reference, but flagged as resolved.
    # We update the related match row if one exists for the same pair.
    related_match = None
    with get_connection() as conn:
        related_match = conn.execute(
            "SELECT id FROM matches WHERE lost_item_id=? AND found_item_id=? ORDER BY id DESC LIMIT 1",
            (lost_item_id, found_item_id),
        ).fetchone()

    if related_match:
        update_match_status(int(related_match["id"]), "resolved")

    return True
