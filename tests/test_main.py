import pytest

from gantt_project_maker.main import check_if_items_are_available

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"


def test_check_beschikbaar():
    """API Tests"""

    input_list = ["A", "B"]
    available_dict = {"A": 0, "B": 1, "C": 2}

    assert check_if_items_are_available(requested_items=input_list, available_items=available_dict)