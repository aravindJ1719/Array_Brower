"""
Pytest tests for the Array Navigation Algorithm Engine.

Covers every rule in the spec:
  - Initial empty state
  - Visit
  - Multiple visits
  - Back
  - Forward
  - Back boundary (already at start)
  - Forward boundary (already at end)
  - Visit after Back (forward history erasure)
  - Reload (read-only — no new array entry)
  - Reset
  - Duplicate URLs
  - Current page
  - Array index boundaries
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.algorithms.array_navigation import ArrayNavigationEngine


# ── Fixtures ────────────────────────────────────────────────────────────── #

@pytest.fixture
def engine():
    """Fresh engine for each test."""
    return ArrayNavigationEngine()


@pytest.fixture
def engine_google(engine):
    """Engine that has visited Google."""
    engine.visit("https://www.google.com")
    return engine


@pytest.fixture
def engine_three(engine):
    """Engine with [Google, YouTube, ChatGPT], current_index=2."""
    engine.visit("https://www.google.com")
    engine.visit("https://www.youtube.com")
    engine.visit("https://chatgpt.com")
    return engine


# ══════════════════════════════════════════════════════════════════════════ #
#  1. Initial empty state
# ══════════════════════════════════════════════════════════════════════════ #

class TestInitialState:
    def test_history_is_empty_list(self, engine):
        assert engine.history == []

    def test_current_index_is_minus_one(self, engine):
        assert engine.current_index == -1

    def test_current_page_is_none(self, engine):
        assert engine.current_page is None

    def test_cannot_go_back(self, engine):
        assert engine.can_go_back is False

    def test_cannot_go_forward(self, engine):
        assert engine.can_go_forward is False

    def test_back_returns_none(self, engine):
        assert engine.back() is None

    def test_forward_returns_none(self, engine):
        assert engine.forward() is None

    def test_reload_returns_none(self, engine):
        assert engine.reload() is None

    def test_get_state_shape(self, engine):
        state = engine.get_state()
        assert state["history"] == []
        assert state["current_index"] == -1
        assert state["current_page"] is None
        assert state["can_go_back"] is False
        assert state["can_go_forward"] is False


# ══════════════════════════════════════════════════════════════════════════ #
#  2. Visit
# ══════════════════════════════════════════════════════════════════════════ #

class TestVisit:
    def test_first_visit_appends_url(self, engine):
        engine.visit("https://www.google.com")
        assert engine.history == ["https://www.google.com"]

    def test_first_visit_sets_index_zero(self, engine):
        engine.visit("https://www.google.com")
        assert engine.current_index == 0

    def test_visit_returns_url(self, engine):
        result = engine.visit("https://www.google.com")
        assert result == "https://www.google.com"

    def test_visit_sets_current_page(self, engine):
        engine.visit("https://www.google.com")
        assert engine.current_page == "https://www.google.com"

    def test_visit_enables_back_after_second(self, engine):
        engine.visit("https://www.google.com")
        assert engine.can_go_back is False  # only one page
        engine.visit("https://www.youtube.com")
        assert engine.can_go_back is True

    def test_visit_does_not_enable_forward(self, engine):
        engine.visit("https://www.google.com")
        engine.visit("https://www.youtube.com")
        assert engine.can_go_forward is False


# ══════════════════════════════════════════════════════════════════════════ #
#  3. Multiple visits
# ══════════════════════════════════════════════════════════════════════════ #

class TestMultipleVisits:
    def test_three_visits_build_array(self, engine_three):
        assert engine_three.history == [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://chatgpt.com",
        ]

    def test_current_index_is_last(self, engine_three):
        assert engine_three.current_index == 2

    def test_current_page_is_last(self, engine_three):
        assert engine_three.current_page == "https://chatgpt.com"

    def test_history_length(self, engine_three):
        assert len(engine_three.history) == 3


# ══════════════════════════════════════════════════════════════════════════ #
#  4. Back
# ══════════════════════════════════════════════════════════════════════════ #

class TestBack:
    def test_back_decrements_index(self, engine_three):
        engine_three.back()
        assert engine_three.current_index == 1

    def test_back_returns_correct_url(self, engine_three):
        result = engine_three.back()
        assert result == "https://www.youtube.com"

    def test_back_twice(self, engine_three):
        engine_three.back()
        result = engine_three.back()
        assert result == "https://www.google.com"
        assert engine_three.current_index == 0

    def test_back_does_not_modify_history_array(self, engine_three):
        original = list(engine_three.history)
        engine_three.back()
        assert engine_three.history == original

    def test_back_enables_forward(self, engine_three):
        engine_three.back()
        assert engine_three.can_go_forward is True


# ══════════════════════════════════════════════════════════════════════════ #
#  5. Forward
# ══════════════════════════════════════════════════════════════════════════ #

class TestForward:
    def test_forward_increments_index(self, engine_three):
        engine_three.back()
        engine_three.forward()
        assert engine_three.current_index == 2

    def test_forward_returns_correct_url(self, engine_three):
        engine_three.back()
        result = engine_three.forward()
        assert result == "https://chatgpt.com"

    def test_forward_twice_after_two_backs(self, engine_three):
        engine_three.back()  # index=1
        engine_three.back()  # index=0
        engine_three.forward()
        result = engine_three.forward()
        assert result == "https://chatgpt.com"
        assert engine_three.current_index == 2

    def test_forward_does_not_modify_history_array(self, engine_three):
        engine_three.back()
        original = list(engine_three.history)
        engine_three.forward()
        assert engine_three.history == original


# ══════════════════════════════════════════════════════════════════════════ #
#  6. Back boundary
# ══════════════════════════════════════════════════════════════════════════ #

class TestBackBoundary:
    def test_back_at_first_page_returns_none(self, engine_google):
        assert engine_google.back() is None

    def test_index_unchanged_at_boundary(self, engine_google):
        engine_google.back()
        assert engine_google.current_index == 0

    def test_back_boundary_on_empty_engine(self, engine):
        assert engine.back() is None
        assert engine.current_index == -1


# ══════════════════════════════════════════════════════════════════════════ #
#  7. Forward boundary
# ══════════════════════════════════════════════════════════════════════════ #

class TestForwardBoundary:
    def test_forward_at_last_page_returns_none(self, engine_three):
        assert engine_three.forward() is None

    def test_index_unchanged_at_forward_boundary(self, engine_three):
        engine_three.forward()
        assert engine_three.current_index == 2

    def test_forward_boundary_on_empty_engine(self, engine):
        assert engine.forward() is None
        assert engine.current_index == -1


# ══════════════════════════════════════════════════════════════════════════ #
#  8. Visit after Back (forward history erasure)
# ══════════════════════════════════════════════════════════════════════════ #

class TestVisitAfterBack:
    def test_forward_history_erased(self, engine_three):
        """
        Google → YouTube → ChatGPT
        Back   → YouTube
        Visit GitHub
        Expected: [Google, YouTube, GitHub], current_index=2
        ChatGPT must be removed.
        """
        engine_three.back()                          # index=1 (YouTube)
        engine_three.visit("https://github.com")     # index=2
        assert engine_three.history == [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://github.com",
        ]
        assert engine_three.current_index == 2
        assert "https://chatgpt.com" not in engine_three.history

    def test_can_go_back_after_new_visit(self, engine_three):
        engine_three.back()
        engine_three.visit("https://github.com")
        assert engine_three.can_go_back is True

    def test_cannot_go_forward_after_new_visit(self, engine_three):
        engine_three.back()
        engine_three.visit("https://github.com")
        assert engine_three.can_go_forward is False

    def test_visit_after_two_backs(self, engine_three):
        """
        Back → index=1, Back → index=0, Visit GitHub
        Expected: [Google, GitHub], ChatGPT & YouTube removed
        """
        engine_three.back()   # index=1
        engine_three.back()   # index=0
        engine_three.visit("https://github.com")
        assert engine_three.history == [
            "https://www.google.com",
            "https://github.com",
        ]
        assert engine_three.current_index == 1


# ══════════════════════════════════════════════════════════════════════════ #
#  9. Reload
# ══════════════════════════════════════════════════════════════════════════ #

class TestReload:
    def test_reload_returns_current_url(self, engine_three):
        result = engine_three.reload()
        assert result == "https://chatgpt.com"

    def test_reload_does_not_change_index(self, engine_three):
        engine_three.reload()
        assert engine_three.current_index == 2

    def test_reload_does_not_add_to_array(self, engine_three):
        before = list(engine_three.history)
        engine_three.reload()
        assert engine_three.history == before

    def test_reload_returns_same_page_after_back(self, engine_three):
        engine_three.back()  # now at YouTube
        result = engine_three.reload()
        assert result == "https://www.youtube.com"


# ══════════════════════════════════════════════════════════════════════════ #
#  10. Reset
# ══════════════════════════════════════════════════════════════════════════ #

class TestReset:
    def test_reset_clears_history(self, engine_three):
        engine_three.reset()
        assert engine_three.history == []

    def test_reset_sets_index_minus_one(self, engine_three):
        engine_three.reset()
        assert engine_three.current_index == -1

    def test_reset_current_page_is_none(self, engine_three):
        engine_three.reset()
        assert engine_three.current_page is None

    def test_can_visit_after_reset(self, engine_three):
        engine_three.reset()
        engine_three.visit("https://www.google.com")
        assert engine_three.history == ["https://www.google.com"]
        assert engine_three.current_index == 0


# ══════════════════════════════════════════════════════════════════════════ #
#  11. Duplicate URLs
# ══════════════════════════════════════════════════════════════════════════ #

class TestDuplicateURLs:
    def test_duplicate_urls_are_allowed(self, engine):
        engine.visit("https://www.google.com")
        engine.visit("https://www.google.com")
        assert len(engine.history) == 2
        assert engine.current_index == 1

    def test_back_on_duplicates(self, engine):
        engine.visit("https://www.google.com")
        engine.visit("https://www.google.com")
        result = engine.back()
        assert result == "https://www.google.com"
        assert engine.current_index == 0


# ══════════════════════════════════════════════════════════════════════════ #
#  12. Current page
# ══════════════════════════════════════════════════════════════════════════ #

class TestCurrentPage:
    def test_current_page_tracks_navigation(self, engine_three):
        assert engine_three.current_page == "https://chatgpt.com"
        engine_three.back()
        assert engine_three.current_page == "https://www.youtube.com"
        engine_three.back()
        assert engine_three.current_page == "https://www.google.com"

    def test_current_page_updates_on_forward(self, engine_three):
        engine_three.back()
        engine_three.forward()
        assert engine_three.current_page == "https://chatgpt.com"


# ══════════════════════════════════════════════════════════════════════════ #
#  13. Array index boundaries
# ══════════════════════════════════════════════════════════════════════════ #

class TestArrayIndexBoundaries:
    def test_current_index_never_goes_below_zero(self, engine):
        for _ in range(5):
            engine.back()
        assert engine.current_index == -1

    def test_current_index_never_exceeds_length_minus_one(self, engine_three):
        for _ in range(10):
            engine_three.forward()
        assert engine_three.current_index == len(engine_three.history) - 1

    def test_current_index_always_valid_reference(self, engine_three):
        """current_index always points to a valid array slot when history is non-empty."""
        engine_three.back()
        engine_three.back()
        assert 0 <= engine_three.current_index < len(engine_three.history)

    def test_get_state_returns_copy_of_history(self, engine_three):
        """get_state() returns a copy; mutating it must not affect the engine."""
        state = engine_three.get_state()
        state["history"].append("https://evil.com")
        assert "https://evil.com" not in engine_three.history


# ══════════════════════════════════════════════════════════════════════════ #
#  14. Full example flow from spec
# ══════════════════════════════════════════════════════════════════════════ #

class TestSpecExampleFlow:
    def test_full_spec_flow(self, engine):
        """
        Replicate the exact flow described in section 11 of the spec:

        Visit Google   → [Google]           index=0
        Visit YouTube  → [Google, YouTube]  index=1
        Visit ChatGPT  → [Google, YouTube, ChatGPT]  index=2
        Back           → index=1  current=YouTube
        Back           → index=0  current=Google
        Forward        → index=1  current=YouTube
        Visit GitHub   → [Google, YouTube, GitHub]  index=2  (ChatGPT erased)
        """
        engine.visit("https://www.google.com")
        assert engine.history == ["https://www.google.com"]
        assert engine.current_index == 0

        engine.visit("https://www.youtube.com")
        assert engine.history == ["https://www.google.com", "https://www.youtube.com"]
        assert engine.current_index == 1

        engine.visit("https://chatgpt.com")
        assert engine.history == [
            "https://www.google.com", "https://www.youtube.com", "https://chatgpt.com"
        ]
        assert engine.current_index == 2

        # Back × 2
        assert engine.back() == "https://www.youtube.com"
        assert engine.current_index == 1
        assert engine.back() == "https://www.google.com"
        assert engine.current_index == 0

        # Forward
        assert engine.forward() == "https://www.youtube.com"
        assert engine.current_index == 1

        # Visit GitHub — ChatGPT must be erased
        engine.visit("https://github.com")
        assert engine.history == [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://github.com",
        ]
        assert engine.current_index == 2
        assert "https://chatgpt.com" not in engine.history
        assert engine.can_go_back is True
        assert engine.can_go_forward is False
