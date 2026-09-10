"""
services/notification_service.py

Sends in-app notifications to the two people on either side of a confirmed
match: the person who lost the item, and the person who found it. This is
intentionally best-effort - a notification failure must never block the
underlying claim/approval workflow that triggered it.
"""

from __future__ import annotations

from typing import Any, Dict

from database.queries import create_notification, get_item, get_user_by_id


def notify_claim_approved(claim: Dict[str, Any]) -> None:
    """Notify both parties that staff has verified their lost/found match.

    Called right after a claim moves to status='approved'. Both the lost-item
    owner and the found-item owner get a notification telling them who the
    other party is and that they should contact staff to arrange the
    handover / further verification.
    """
    lost = get_item(claim["lost_item_id"])
    found = get_item(claim["found_item_id"])
    if not lost or not found:
        return

    lost_owner_id = lost.get("user_id")
    found_owner_id = found.get("user_id")

    lost_owner = get_user_by_id(lost_owner_id) if lost_owner_id else None
    found_owner = get_user_by_id(found_owner_id) if found_owner_id else None

    lost_owner_name = lost_owner["full_name"] if lost_owner else "another user"
    found_owner_name = found_owner["full_name"] if found_owner else "another user"

    if lost_owner_id:
        create_notification(
            user_id=lost_owner_id,
            title="Your lost item has been found! 🎉",
            message=(
                f'Great news — your lost item "{lost["title"]}" has been matched with an item '
                f"found by {found_owner_name}. Please contact staff to verify and arrange the handover."
            ),
            notif_type="match_confirmed",
            item_id=lost["id"],
            claim_id=claim["id"],
        )

    if found_owner_id and found_owner_id != lost_owner_id:
        create_notification(
            user_id=found_owner_id,
            title="The item you found has an owner! 🎉",
            message=(
                f'The item you found, "{found["title"]}", has been matched with a lost-item report '
                f"from {lost_owner_name}. Please contact staff to verify and arrange the handover."
            ),
            notif_type="match_confirmed",
            item_id=found["id"],
            claim_id=claim["id"],
        )
