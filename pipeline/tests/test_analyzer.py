from pipeline.src.analyzer import (
    _filter_tokens,
    _impute_dead_tokens,
    compute_summary,
    compute_sensitivity,
)


def _make_token(cycle_type="Bull", annualized_roi=0.5, roi_since_launch=1.0,
                roi_vs_btc=0.3, category="Other", **overrides):
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
        "category": category,
        "cycle_type": cycle_type,
        "cycle_name": "2020-2021 Bull",
        "age_days": 1460,
        "roi_since_launch": roi_since_launch,
        "annualized_roi": annualized_roi,
        "roi_vs_btc": roi_vs_btc,
        "drawdown_from_ath": 0.5,
        "binance_listed": True,
        "binance_delisted": False,
        "binance_delist_date": None,
    }
    base.update(overrides)
    return base


class TestFilterTokens:
    def test_excludes_stablecoins(self):
        tokens = [
            _make_token(category="Stablecoin"),
            _make_token(category="Other"),
        ]
        filtered, n_stable, n_wrapped = _filter_tokens(tokens)
        assert len(filtered) == 1
        assert n_stable == 1
        assert n_wrapped == 0

    def test_excludes_wrapped(self):
        tokens = [
            _make_token(category="Wrapped"),
            _make_token(category="L1"),
        ]
        filtered, n_stable, n_wrapped = _filter_tokens(tokens)
        assert len(filtered) == 1
        assert n_stable == 0
        assert n_wrapped == 1

    def test_keeps_normal_tokens(self):
        tokens = [
            _make_token(category="DeFi"),
            _make_token(category="L1"),
            _make_token(category="Other"),
        ]
        filtered, n_stable, n_wrapped = _filter_tokens(tokens)
        assert len(filtered) == 3


class TestImputeDeadTokens:
    def test_imputes_delisted_no_price(self):
        token = _make_token(
            binance_delisted=True,
            current_price=None,
            roi_since_launch=None,
            annualized_roi=None,
            age_days=730,
        )
        count = _impute_dead_tokens([token])
        assert count == 1
        assert token["roi_since_launch"] == -1.0
        assert token["annualized_roi"] == -1.0

    def test_imputes_roi_but_not_annualized_for_young_tokens(self):
        token = _make_token(
            binance_delisted=True,
            current_price=None,
            roi_since_launch=None,
            annualized_roi=None,
            age_days=200,
        )
        count = _impute_dead_tokens([token])
        assert count == 1
        assert token["roi_since_launch"] == -1.0
        assert token["annualized_roi"] is None  # too young for CAGR

    def test_skips_delisted_with_price(self):
        token = _make_token(
            binance_delisted=True,
            current_price=0.5,
            roi_since_launch=-0.95,
        )
        count = _impute_dead_tokens([token])
        assert count == 0
        assert token["roi_since_launch"] == -0.95

    def test_skips_active_tokens(self):
        token = _make_token(binance_delisted=False, roi_since_launch=None, current_price=None)
        count = _impute_dead_tokens([token])
        assert count == 0


class TestComputeSummary:
    def test_empty_tokens(self):
        summary = compute_summary([])
        assert summary.total_tokens == 0
        assert summary.bull_vs_bear_mannwhitney_pvalue is None

    def test_basic_computation(self):
        tokens = (
            [_make_token(id=f"bull-{i}", cycle_type="Bull", annualized_roi=0.5 + i * 0.01)
             for i in range(25)]
            + [_make_token(id=f"bear-{i}", cycle_type="Bear", annualized_roi=0.3 + i * 0.01,
                           cycle_name="2022 Bear")
               for i in range(25)]
        )
        summary = compute_summary(tokens)
        assert summary.total_tokens == 50
        assert summary.bull_n == 25
        assert summary.bear_n == 25
        assert summary.bull_vs_bear_mannwhitney_pvalue is not None

    def test_stablecoins_excluded_from_count(self):
        tokens = [
            _make_token(category="Stablecoin"),
            _make_token(category="Other"),
        ]
        summary = compute_summary(tokens)
        assert summary.total_tokens == 1
        assert summary.tokens_excluded_stablecoin == 1

    def test_too_few_samples_no_test(self):
        """With fewer than 20 per group, statistical tests should return None."""
        tokens = (
            [_make_token(id=f"bull-{i}", cycle_type="Bull") for i in range(5)]
            + [_make_token(id=f"bear-{i}", cycle_type="Bear", cycle_name="2022 Bear") for i in range(5)]
        )
        summary = compute_summary(tokens)
        assert summary.bull_vs_bear_mannwhitney_pvalue is None


class TestComputeSensitivity:
    def test_returns_five_entries_with_effect_sizes(self):
        tokens = (
            [_make_token(id=f"bull-{i}", cycle_type="Bull", launch_date="2020-06-01")
             for i in range(25)]
            + [_make_token(id=f"bear-{i}", cycle_type="Bear", launch_date="2022-06-01",
                           cycle_name="2022 Bear")
               for i in range(25)]
        )
        result = compute_sensitivity(tokens)
        assert len(result) == 5
        shifts = [r["shift_months"] for r in result]
        assert shifts == [-2, -1, 0, 1, 2]
        # Each entry should include effect_size
        for r in result:
            assert "effect_size" in r

    def test_zero_shift_matches_main_analysis(self):
        tokens = (
            [_make_token(id=f"bull-{i}", cycle_type="Bull", annualized_roi=0.5,
                         launch_date="2020-06-01")
             for i in range(25)]
            + [_make_token(id=f"bear-{i}", cycle_type="Bear", annualized_roi=0.5,
                           launch_date="2022-06-01", cycle_name="2022 Bear")
               for i in range(25)]
        )
        result = compute_sensitivity(tokens)
        zero_shift = [r for r in result if r["shift_months"] == 0][0]
        # With identical ROIs, p-value should be high (not significant)
        if zero_shift["pvalue"] is not None:
            assert not zero_shift["significant"]
