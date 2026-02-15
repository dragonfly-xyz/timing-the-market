from datetime import date
from pipeline.src.metrics import compute_metrics


def _make_token(**overrides):
    base = {
        "id": "test",
        "symbol": "TEST",
        "name": "Test Token",
        "current_price": 100.0,
        "market_cap": 1_000_000,
        "market_cap_rank": 50,
        "ath": 200.0,
        "atl": 1.0,
        "image": None,
        "launch_date": "2020-06-01",
        "launch_price": 10.0,
        "launch_source": "genesis_date",
        "categories": [],
        "category": "Other",
    }
    base.update(overrides)
    return base


def test_roi_calculation():
    token = _make_token(launch_price=10.0, current_price=100.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] == 9.0  # (100-10)/10


def test_roi_none_when_no_launch_price():
    token = _make_token(launch_price=None)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] is None


def test_age_days():
    token = _make_token(launch_date="2024-01-01")
    result = compute_metrics([token], today=date(2024, 7, 1))[0]
    assert result["age_days"] == 182  # Jan 1 to Jul 1


def test_drawdown_from_ath():
    token = _make_token(ath=200.0, current_price=50.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["drawdown_from_ath"] == 0.75  # (200-50)/200


def test_cycle_classification():
    token = _make_token(launch_date="2020-06-01")
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["cycle_type"] == "Bull"
    assert result["cycle_name"] == "2020-2021 Bull"


def test_annualized_roi():
    # 10x over 4 years → CAGR = 10^(1/4) - 1 ≈ 0.778
    token = _make_token(launch_price=10.0, current_price=100.0, launch_date="2020-06-01")
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["annualized_roi"] is not None
    assert 0.7 < result["annualized_roi"] < 0.85


def test_no_launch_date():
    token = _make_token(launch_date=None, launch_price=None)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["cycle_type"] == "Unknown"
    assert result["age_days"] is None
    assert result["roi_since_launch"] is None


# --- New edge case tests ---

def test_dead_token_current_price_zero():
    """Token with current_price=0 should get -100% ROI, not be excluded."""
    token = _make_token(launch_price=10.0, current_price=0.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] == -1.0  # (0-10)/10 = -100%


def test_dead_token_btc_relative_not_excluded():
    """Token with current_price=0 should still get a BTC-relative metric."""
    # This test can't compute BTC-relative without btc_chart.json, but it should
    # not crash and should produce roi_since_launch = -1.0
    token = _make_token(launch_price=10.0, current_price=0.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] == -1.0


def test_young_token_no_annualized_roi():
    """Token under 365 days old should have annualized_roi = None."""
    token = _make_token(launch_price=10.0, current_price=20.0, launch_date="2024-03-01")
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] == 1.0  # (20-10)/10
    assert result["annualized_roi"] is None  # only 92 days old


def test_drawdown_zero_when_price_above_ath():
    """When current_price > ath, drawdown should be 0, not negative."""
    token = _make_token(ath=100.0, current_price=150.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["drawdown_from_ath"] == 0.0


def test_launch_price_zero_gives_none_roi():
    """launch_price=0 should give roi_since_launch=None (division by zero guard)."""
    token = _make_token(launch_price=0.0, current_price=100.0)
    result = compute_metrics([token], today=date(2024, 6, 1))[0]
    assert result["roi_since_launch"] is None
