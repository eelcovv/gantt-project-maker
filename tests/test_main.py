import pytest

from gantt_project_maker.main import check_if_items_are_available

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"


def test_check_if_items_are_available():
    """API Tests if check succeeds"""

    input_list = ["A", "B"]
    available_dict = {"A": 0, "B": 1, "C": 2}

    assert check_if_items_are_available(
        requested_items=input_list, available_items=available_dict, label="test1"
    )


def test_check_if_items_are_available_error():
    """API Tests if check files. Should raise a value error"""

    input_list = ["A", "B", "D"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    with pytest.raises(ValueError):
        check_if_items_are_available(
            requested_items=input_list, available_items=available_dict, label="test2"
        )
