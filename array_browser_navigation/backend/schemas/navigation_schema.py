"""
Pydantic schemas for request/response validation.
"""

from typing import Optional
from pydantic import BaseModel, field_validator

# Well-known short names → full URLs
_SHORTCUTS: dict[str, str] = {
    "google":     "https://www.google.com",
    "youtube":    "https://www.youtube.com",
    "chatgpt":    "https://chatgpt.com",
    "github":     "https://github.com",
    "facebook":   "https://www.facebook.com",
    "instagram":  "https://www.instagram.com",
    "twitter":    "https://twitter.com",
    "x":          "https://x.com",
    "reddit":     "https://www.reddit.com",
    "wikipedia":  "https://www.wikipedia.org",
    "stackoverflow": "https://stackoverflow.com",
    "linkedin":   "https://www.linkedin.com",
    "amazon":     "https://www.amazon.com",
    "netflix":    "https://www.netflix.com",
    "whatsapp":   "https://web.whatsapp.com",
}


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class VisitRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def normalise_url(cls, v: str) -> str:
        v = v.strip()

        # Check shortcuts first (e.g. "youtube" → full URL)
        lower = v.lower().rstrip("/")
        if lower in _SHORTCUTS:
            return _SHORTCUTS[lower]

        # Already has a scheme
        if v.startswith(("http://", "https://")):
            return v

        # Has a dot → treat as domain (e.g. "youtube.com")
        if "." in v:
            return "https://" + v

        # Bare word with no dot → assume .com (e.g. "youtube" missed above)
        return f"https://www.{v}.com"


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class NavigationState(BaseModel):
    """Full state snapshot returned by every navigation endpoint."""

    history: list[str]
    current_index: int
    current_page: Optional[str]
    can_go_back: bool
    can_go_forward: bool

    model_config = {"from_attributes": True}


class NavigationResult(BaseModel):
    """Wraps NavigationState with an action label and optional message."""

    action: str
    success: bool
    message: str
    state: NavigationState


class HistoryEntry(BaseModel):
    """One row returned from the database history endpoint."""

    index: int
    url: str
    is_current: bool


class HistoryResponse(BaseModel):
    """Full /history response including both array state and DB records."""

    array_state: NavigationState
    db_records: list[HistoryEntry]
    total_entries: int


class AlgorithmRules(BaseModel):
    """Describes the array navigation algorithm in human-readable form."""

    data_structure: str
    state_variables: dict[str, str]
    algorithm_rules: dict[str, str]
    key_invariants: list[str]
