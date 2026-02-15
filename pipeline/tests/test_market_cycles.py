from datetime import date
from pipeline.src.market_cycles import classify_launch_date, get_cycle_type, get_cycle_name


def test_bitcoin_genesis():
    # Bitcoin genesis: Jan 3, 2009 — should be "Pre-2013 Early"
    d = date(2009, 1, 3)
    assert get_cycle_type(d) == "Early"
    assert get_cycle_name(d) == "Pre-2013 Early"


def test_2013_bull():
    d = date(2013, 6, 15)
    assert get_cycle_type(d) == "Bull"
    assert get_cycle_name(d) == "2013 Bull"


def test_2014_bear():
    d = date(2014, 6, 1)
    assert get_cycle_type(d) == "Bear"


def test_2017_bull():
    d = date(2017, 6, 1)
    assert get_cycle_type(d) == "Bull"
    assert get_cycle_name(d) == "2016-2017 Bull"


def test_2018_bear():
    d = date(2018, 6, 1)
    assert get_cycle_type(d) == "Bear"


def test_2020_bull():
    d = date(2020, 8, 1)
    assert get_cycle_type(d) == "Bull"
    assert get_cycle_name(d) == "2020-2021 Bull"


def test_2022_bear():
    d = date(2022, 3, 1)
    assert get_cycle_type(d) == "Bear"


def test_2023_recovery():
    d = date(2023, 5, 1)
    assert get_cycle_type(d) == "Neutral"


def test_2024_bull():
    d = date(2024, 6, 1)
    assert get_cycle_type(d) == "Bull"
    assert get_cycle_name(d) == "2023-2025 Bull"


def test_none_date():
    assert get_cycle_type(None) == "Unknown"
    assert get_cycle_name(None) == "Unknown"


def test_boundary_2013_start():
    # Exactly Jan 1, 2013 should be 2013 Bull
    d = date(2013, 1, 1)
    assert get_cycle_type(d) == "Bull"


def test_boundary_2013_end():
    # Dec 1, 2013 should be start of Bear
    d = date(2013, 12, 1)
    assert get_cycle_type(d) == "Bear"
