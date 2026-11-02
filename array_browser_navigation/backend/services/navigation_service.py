"""
Navigation Service
==================
Bridges the Array Algorithm Engine ↔ FastAPI ↔ MySQL.

Responsibilities:
  1. Delegate every navigation decision to the ArrayNavigationEngine.
  2. Persist the resulting array state to MySQL (for durability / demo).
  3. Build Pydantic response objects for the API layer.

The service NEVER implements navigation logic itself — it always delegates
to `navigation_engine` (the Array Algorithm Engine singleton).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.algorithms.array_navigation import navigation_engine
from backend.database.models import NavigationHistory
from backend.schemas.navigation_schema import (
    NavigationResult,
    NavigationState,
    HistoryEntry,
    HistoryResponse,
)

# A fixed session identifier for single-user demo purposes.
SESSION_ID = "default_session"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _state_snapshot() -> NavigationState:
    """Convert the engine's current state dict into a Pydantic model."""
    return NavigationState(**navigation_engine.get_state())


def _persist_array_to_db(db: Session) -> None:
    """
    Overwrite the DB records for this session to mirror the in-memory array.

    Approach:
      • Delete all existing rows for SESSION_ID.
      • Re-insert one row per array entry, marking the current page.

    This keeps MySQL in sync with the Python array after every navigation action.
    """
    # Remove stale rows
    db.query(NavigationHistory).filter(
        NavigationHistory.session_id == SESSION_ID
    ).delete(synchronize_session=False)

    now = datetime.now(timezone.utc)

    # Insert fresh rows mirroring history[]
    for idx, url in enumerate(navigation_engine.history):
        row = NavigationHistory(
            session_id=SESSION_ID,
            page_url=url,
            position_index=idx,
            is_current=(idx == navigation_engine.current_index),
            created_at=now,
            updated_at=now,
        )
        db.add(row)

    db.commit()


# ---------------------------------------------------------------------------
# Public service methods (called by API routes)
# ---------------------------------------------------------------------------

def visit_url(url: str, db: Session) -> NavigationResult:
    """
    Tell the Array Algorithm Engine to visit a new URL.
    Persist the new array state to MySQL.
    Return a NavigationResult.
    """
    navigation_engine.visit(url)
    _persist_array_to_db(db)

    return NavigationResult(
        action="visit",
        success=True,
        message=f"Navigated to {url}",
        state=_state_snapshot(),
    )


def go_back(db: Session) -> NavigationResult:
    """Delegate Back to the engine, persist, return result."""
    url = navigation_engine.back()

    if url is None:
        return NavigationResult(
            action="back",
            success=False,
            message="Already at the beginning of history — cannot go back.",
            state=_state_snapshot(),
        )

    _persist_array_to_db(db)
    return NavigationResult(
        action="back",
        success=True,
        message=f"Went back to {url}",
        state=_state_snapshot(),
    )


def go_forward(db: Session) -> NavigationResult:
    """Delegate Forward to the engine, persist, return result."""
    url = navigation_engine.forward()

    if url is None:
        return NavigationResult(
            action="forward",
            success=False,
            message="Already at the end of history — cannot go forward.",
            state=_state_snapshot(),
        )

    _persist_array_to_db(db)
    return NavigationResult(
        action="forward",
        success=True,
        message=f"Went forward to {url}",
        state=_state_snapshot(),
    )


def reload_page(db: Session) -> NavigationResult:
    """
    Reload the current page.
    The array is NOT modified — this is a read-only operation.
    """
    url = navigation_engine.reload()

    if url is None:
        return NavigationResult(
            action="reload",
            success=False,
            message="No page to reload — history is empty.",
            state=_state_snapshot(),
        )

    # No DB write needed: array didn't change.
    return NavigationResult(
        action="reload",
        success=True,
        message=f"Reloaded {url}",
        state=_state_snapshot(),
    )


def reset_navigation(db: Session) -> NavigationResult:
    """Clear the array and wipe the DB session records."""
    navigation_engine.reset()
    _persist_array_to_db(db)  # persists empty state

    return NavigationResult(
        action="reset",
        success=True,
        message="Navigation history cleared.",
        state=_state_snapshot(),
    )


def get_history(db: Session) -> HistoryResponse:
    """
    Return both the in-memory array state and the persisted DB records.
    Useful for monitoring / demo purposes.
    """
    db_rows = (
        db.query(NavigationHistory)
        .filter(NavigationHistory.session_id == SESSION_ID)
        .order_by(NavigationHistory.position_index)
        .all()
    )

    db_records = [
        HistoryEntry(
            index=row.position_index,
            url=row.page_url,
            is_current=row.is_current,
        )
        for row in db_rows
    ]

    return HistoryResponse(
        array_state=_state_snapshot(),
        db_records=db_records,
        total_entries=len(db_records),
    )
