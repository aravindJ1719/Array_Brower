"""
FastAPI navigation routes.
All routes delegate to the Navigation Service, which in turn
delegates to the Array Algorithm Engine.

No navigation logic lives here.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.schemas.navigation_schema import (
    VisitRequest,
    NavigationResult,
    HistoryResponse,
    AlgorithmRules,
)
from backend.services import navigation_service
from backend.algorithms.array_navigation import navigation_engine

router = APIRouter()


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get full navigation history",
    description=(
        "Returns the current in-memory array state plus the persisted "
        "MySQL records for this session."
    ),
)
def get_history(db: Session = Depends(get_db)) -> HistoryResponse:
    return navigation_service.get_history(db)


@router.get(
    "/algorithm/rules",
    response_model=AlgorithmRules,
    summary="Describe the Array Navigation Algorithm",
    description=(
        "Returns a human-readable explanation of the array-based "
        "navigation algorithm — data structure, state variables, and rules."
    ),
)
def algorithm_rules() -> AlgorithmRules:
    raw = navigation_engine.get_algorithm_rules()
    return AlgorithmRules(**raw)


# ---------------------------------------------------------------------------
# POST endpoints — navigation actions
# ---------------------------------------------------------------------------

@router.post(
    "/visit",
    response_model=NavigationResult,
    summary="Visit a URL",
    description=(
        "Navigate to a new URL. The Array Algorithm Engine truncates forward "
        "history and appends the new URL to the array."
    ),
)
def visit(request: VisitRequest, db: Session = Depends(get_db)) -> NavigationResult:
    return navigation_service.visit_url(request.url, db)


@router.post(
    "/back",
    response_model=NavigationResult,
    summary="Go Back",
    description=(
        "Move current_index one step backward in the history array. "
        "Returns the URL now pointed to by current_index."
    ),
)
def back(db: Session = Depends(get_db)) -> NavigationResult:
    return navigation_service.go_back(db)


@router.post(
    "/forward",
    response_model=NavigationResult,
    summary="Go Forward",
    description=(
        "Move current_index one step forward in the history array. "
        "Returns the URL now pointed to by current_index."
    ),
)
def forward(db: Session = Depends(get_db)) -> NavigationResult:
    return navigation_service.go_forward(db)


@router.post(
    "/reload",
    response_model=NavigationResult,
    summary="Reload current page",
    description=(
        "Return the URL at current_index without modifying the array. "
        "No new entry is created."
    ),
)
def reload(db: Session = Depends(get_db)) -> NavigationResult:
    return navigation_service.reload_page(db)


@router.post(
    "/reset",
    response_model=NavigationResult,
    summary="Reset navigation history",
    description="Clear the history array, set current_index = -1, wipe DB records.",
)
def reset(db: Session = Depends(get_db)) -> NavigationResult:
    return navigation_service.reset_navigation(db)
