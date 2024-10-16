import pytest

from gantt_project_maker.main import check_if_items_are_available


def test_check_if_items_are_available():
    """
    Test that check_if_items_are_available returns True when all items in input_list are available in available_dict.
    """
    input_list = ["A", "B"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    assert check_if_items_are_available(input_list, available_dict, "test1")


def test_check_if_items_are_available_error():
    """
    Test that check_if_items_are_available raises a ValueError when an item in input_list is not available in available_dict.
    """
    input_list = ["A", "B", "D"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    with pytest.raises(ValueError):
        check_if_items_are_available(input_list, available_dict, "test2")


def check_if_items_are_available_all_items_present():
    """
    Test that check_if_items_are_available returns True when all items in input_list are available in available_dict.
    """
    input_list = ["A", "B"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    assert check_if_items_are_available(input_list, available_dict, "test1")


def check_if_items_are_available_item_missing():
    """
    Test that check_if_items_are_available raises a ValueError when an item in input_list is not available in available_dict.
    """
    input_list = ["A", "B", "D"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    with pytest.raises(ValueError):
        check_if_items_are_available(input_list, available_dict, "test2")


def check_if_items_are_available_empty_input_list():
    """
    Test that check_if_items_are_available returns True when input_list is empty.
    """
    input_list = []
    available_dict = {"A": 0, "B": 1, "C": 2}
    assert check_if_items_are_available(input_list, available_dict, "test3")


def check_if_items_are_available_empty_available_dict():
    """
    Test that check_if_items_are_available raises a ValueError when available_dict is empty.
    """
    input_list = ["A", "B"]
    available_dict = {}
    with pytest.raises(ValueError):
        check_if_items_are_available(input_list, available_dict, "test4")


def check_if_items_are_available_partial_match():
    """
    Test that check_if_items_are_available raises a ValueError when only some items in input_list are available in available_dict.
    """
    input_list = ["A", "D"]
    available_dict = {"A": 0, "B": 1, "C": 2}
    with pytest.raises(ValueError):
        check_if_items_are_available(input_list, available_dict, "test5")
