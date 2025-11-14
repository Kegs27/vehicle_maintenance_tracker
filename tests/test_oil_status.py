def make_status(best_miles=None, best_days=None):
    """Helper mirroring oil reminder threshold logic."""
    SOON_MILES, SOON_DAYS = 500, 30
    DUE_MILES, DUE_DAYS = 50, 5

    state = "ok"

    if (
        (best_miles is not None and best_miles <= DUE_MILES)
        or (best_days is not None and best_days <= DUE_DAYS)
    ):
        state = "due"
    elif (
        (best_miles is not None and best_miles <= SOON_MILES)
        or (best_days is not None and best_days <= SOON_DAYS)
    ):
        state = "soon"

    return state


def test_due_by_miles_before_target():
    assert make_status(best_miles=50, best_days=None) == "due"
    assert make_status(best_miles=0, best_days=None) == "due"
    assert make_status(best_miles=-10, best_days=None) == "due"
    assert make_status(best_miles=51, best_days=None) == "soon"


def test_due_by_days_before_target():
    assert make_status(best_miles=None, best_days=5) == "due"
    assert make_status(best_miles=None, best_days=0) == "due"
    assert make_status(best_miles=None, best_days=-2) == "due"
    assert make_status(best_miles=None, best_days=6) == "soon"


def test_soon_only_by_miles_or_days():
    assert make_status(best_miles=500, best_days=None) == "soon"
    assert make_status(best_miles=None, best_days=30) == "soon"


def test_ok_when_far_out():
    assert make_status(best_miles=800, best_days=None) == "ok"
    assert make_status(best_miles=None, best_days=60) == "ok"


def test_either_or_picks_due_if_any_due():
    assert make_status(best_miles=400, best_days=4) == "due"  # days near limit
    assert make_status(best_miles=40, best_days=40) == "due"  # miles near limit


def test_either_or_picks_soon_if_no_due():
    assert make_status(best_miles=400, best_days=40) == "soon"
    assert make_status(best_miles=60, best_days=20) == "soon"

