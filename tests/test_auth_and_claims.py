import os
import sqlite3

from database.database import DB_PATH, init_db
from database.queries import get_user_by_username, get_claim_by_pair, get_item
from services.claim_service import create_claim_for_match, resolve_claim_handover
from utils.security import hash_password, verify_password


def setup_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def test_default_users_are_seeded_and_hashed():
    admin = get_user_by_username("admin")
    assert admin is not None
    assert admin["role"] == "Administrator"
    assert verify_password("Admin@123", admin["password_hash"]) is True
    assert "Admin@123" not in admin["password_hash"]

    staff = get_user_by_username("staff")
    assert staff is not None
    assert staff["role"] == "Staff"

    regular = get_user_by_username("user1")
    assert regular is not None
    assert regular["role"] == "Regular User"


def test_claim_resolution_marks_items_closed_and_prevents_repeat_claims():
    from database.queries import insert_item

    lost_id = insert_item("lost", "Wallet", "Brown leather wallet", "wallet", "Guess", "brown", "Library", "2026-09-09", "10:30", None)
    found_id = insert_item("found", "Wallet", "Brown leather wallet found", "wallet", "Guess", "brown", "Library", "2026-09-09", "11:00", None)

    claim_id = create_claim_for_match(lost_id, found_id, requested_by_user_id=3, notes="Test claim")
    assert claim_id is not None
    assert get_claim_by_pair(lost_id, found_id)["status"] == "potential"

    resolve_claim_handover(claim_id, reviewed_by_user_id=2, notes="Verified by staff")

    lost = get_item(lost_id)
    found = get_item(found_id)
    final_claim = get_claim_by_pair(lost_id, found_id)

    assert lost["status"] == "resolved"
    assert found["status"] == "resolved"
    assert final_claim["status"] == "resolved"
    assert final_claim["verification_status"] == "approved"
    assert final_claim["handover_status"] == "handed_over"

    duplicate = create_claim_for_match(lost_id, found_id, requested_by_user_id=4, notes="Duplicate")
    assert duplicate is None
