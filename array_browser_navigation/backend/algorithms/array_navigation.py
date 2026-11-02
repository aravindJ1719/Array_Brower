"""
Array Navigation Algorithm Engine
===================================
This is the brain of the browser's navigation system.

All Back / Forward / Visit decisions are made here using:
    history = []          (Python List / Array)
    current_index = -1    (integer pointer into the array)

No Stack, Queue, Linked List, or Browser History API is used.
The array itself IS the navigation engine.
"""

from typing import Optional


class ArrayNavigationEngine:
    """
    Pure Array-based navigation algorithm.

    State:
        history       : list[str]  — ordered list of visited URLs
        current_index : int        — pointer to the current page in the array
    """

    def __init__(self) -> None:
        self.history: list[str] = []
        self.current_index: int = -1

    # ------------------------------------------------------------------
    # Core Algorithm Methods
    # ------------------------------------------------------------------

    def visit(self, url: str) -> str:
        """
        Visit a new URL.

        Algorithm:
            1. Truncate any forward history (everything after current_index).
            2. Append the new URL to the array.
            3. Advance current_index to point at the new page.

        This ensures that after going Back and then visiting a new page,
        the forward history is erased — just like a real browser.
        """
        # Step 1 – remove forward history
        self.history = self.history[: self.current_index + 1]

        # Step 2 – add new page
        self.history.append(url)

        # Step 3 – move pointer forward
        self.current_index = len(self.history) - 1

        return self.history[self.current_index]

    def back(self) -> Optional[str]:
        """
        Navigate backward by decrementing current_index.

        Algorithm:
            if current_index > 0:
                current_index -= 1
                return history[current_index]

        Returns None if already at the beginning of the array.
        """
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None  # already at the start – cannot go further back

    def forward(self) -> Optional[str]:
        """
        Navigate forward by incrementing current_index.

        Algorithm:
            if current_index < len(history) - 1:
                current_index += 1
                return history[current_index]

        Returns None if already at the end of the array.
        """
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None  # already at the end – no forward history

    def reload(self) -> Optional[str]:
        """
        Reload the current page.

        Algorithm:
            return history[current_index]   (no index change, no new array entry)

        This is a read-only operation — the array and index are NOT modified.
        """
        if self.current_index >= 0:
            return self.history[self.current_index]
        return None

    def reset(self) -> None:
        """
        Clear all navigation history and reset to initial state.

        Algorithm:
            history = []
            current_index = -1
        """
        self.history = []
        self.current_index = -1

    # ------------------------------------------------------------------
    # State Inspection (read-only helpers)
    # ------------------------------------------------------------------

    @property
    def current_page(self) -> Optional[str]:
        """Return the URL at current_index, or None if history is empty."""
        if self.current_index >= 0 and self.current_index < len(self.history):
            return self.history[self.current_index]
        return None

    @property
    def can_go_back(self) -> bool:
        """True when there is at least one page before current_index."""
        return self.current_index > 0

    @property
    def can_go_forward(self) -> bool:
        """True when there is at least one page after current_index."""
        return self.current_index < len(self.history) - 1

    def get_state(self) -> dict:
        """
        Return a full snapshot of the current navigation state.
        Used by FastAPI routes to build JSON responses.
        """
        return {
            "history": list(self.history),          # copy so callers can't mutate
            "current_index": self.current_index,
            "current_page": self.current_page,
            "can_go_back": self.can_go_back,
            "can_go_forward": self.can_go_forward,
        }

    def get_algorithm_rules(self) -> dict:
        """
        Return a human-readable description of the array navigation algorithm.
        Useful for educational / interview demonstrations.
        """
        return {
            "data_structure": "Python List (Array)",
            "state_variables": {
                "history": "list[str] — stores every visited URL in order",
                "current_index": "int — pointer to the currently active page",
            },
            "algorithm_rules": {
                "visit": (
                    "history = history[:current_index + 1]  # truncate forward history\n"
                    "history.append(new_url)               # add new page\n"
                    "current_index = len(history) - 1      # advance pointer"
                ),
                "back": (
                    "if current_index > 0:\n"
                    "    current_index -= 1\n"
                    "return history[current_index]"
                ),
                "forward": (
                    "if current_index < len(history) - 1:\n"
                    "    current_index += 1\n"
                    "return history[current_index]"
                ),
                "reload": (
                    "return history[current_index]  # read-only; array unchanged"
                ),
                "reset": (
                    "history = []\n"
                    "current_index = -1"
                ),
            },
            "key_invariants": [
                "Array index always points to the active URL.",
                "Forward history is erased when a new URL is visited after going Back.",
                "Reload never creates a new array entry.",
                "Back/Forward only move the pointer; they never modify the array.",
            ],
        }


# Singleton instance shared across the FastAPI application lifetime.
# A fresh instance means a fresh navigation session on server start.
navigation_engine = ArrayNavigationEngine()
