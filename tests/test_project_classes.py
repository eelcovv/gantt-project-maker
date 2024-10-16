import pytest
import dateutil.parser as dparse
from gantt_project_maker.project_classes import get_nearest_saturday, parse_date


def test_parse_date():
    """
    Test that parse_date correctly parses a valid date string and returns the expected date object.
    """
    date = "25-12-2023"
    parsed_date = dparse.parse(date, dayfirst=True).date()
    assert parse_date(date, dayfirst=True) == parsed_date
    assert parse_date(None, date_default=date, dayfirst=True) == parsed_date


def test_nearest_saturday():
    """
    Test that get_nearest_saturday returns the nearest Saturday for given dates.
    """
    date1 = parse_date("25-12-2023", dayfirst=True)
    date2 = parse_date("28-12-2023", dayfirst=True)
    assert get_nearest_saturday(date1) == parse_date("23-12-2023", dayfirst=True)
    assert get_nearest_saturday(date2) == parse_date("30-12-2023", dayfirst=True)


def parse_date_valid_date():
    """
    Test that parse_date correctly parses a valid date string and returns the expected date object.
    """
    date = "01-01-2023"
    parsed_date = dparse.parse(date, dayfirst=True).date()
    assert parse_date(date, dayfirst=True) == parsed_date


def parse_date_invalid_date():
    """
    Test that parse_date raises a ValueError when given an invalid date string.
    """
    with pytest.raises(ValueError):
        parse_date("invalid-date", dayfirst=True)


def parse_date_none_with_default():
    """
    Test that parse_date returns the default date when given None as input.
    """
    date = "01-01-2023"
    parsed_date = dparse.parse(date, dayfirst=True).date()
    assert parse_date(None, date_default=date, dayfirst=True) == parsed_date


def nearest_saturday_before_date():
    """
    Test that get_nearest_saturday returns the nearest Saturday before the given date.
    """
    date = parse_date("01-01-2023", dayfirst=True)
    assert get_nearest_saturday(date) == parse_date("31-12-2022", dayfirst=True)


def nearest_saturday_after_date():
    """
    Test that get_nearest_saturday returns the nearest Saturday after the given date.
    """
    date = parse_date("02-01-2023", dayfirst=True)
    assert get_nearest_saturday(date) == parse_date("07-01-2023", dayfirst=True)


def nearest_saturday_on_saturday():
    """
    Test that get_nearest_saturday returns the same date when the given date is a Saturday.
    """
    date = parse_date("07-01-2023", dayfirst=True)
    assert get_nearest_saturday(date) == date
