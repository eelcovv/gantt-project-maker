import pytest
import dateutil.parser as dparse

from gantt_project_maker.project_classes import get_nearest_saturday, parse_date

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"


def test_parse_date():
    date = "25-12-2023"
    assert parse_date(date, dayfirst=True) == dparse.parse(date, dayfirst=True).date()
    assert (
        parse_date(None, date_default=date, dayfirst=True)
        == dparse.parse(date, dayfirst=True).date()
    )


def test_nearest_saturday():
    """API Tests if check succeeds"""

    date = parse_date("25-12-2023", dayfirst=True)
    assert get_nearest_saturday(date) == parse_date("23-12-2023", dayfirst=True)

    date = parse_date("28-12-2023", dayfirst=True)
    assert get_nearest_saturday(date) == parse_date("30-12-2023", dayfirst=True)
