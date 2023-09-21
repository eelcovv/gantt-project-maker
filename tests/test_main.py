import pytest

from gantt_project_maker.main import main, check_beschikbaar

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"


def test_check_beschikbaar():
    """API Tests"""

    input_list = ["A", "B"]
    available_dict = {"A": 0, "B": 1, "C": 2}

    assert check_beschikbaar(gevraagd=input_list, beschikbaar=available_dict)