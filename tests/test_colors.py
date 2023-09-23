import pytest

from gantt_project_maker.colors import hex_number_to_hex_hash, color_to_hex

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"


def test_hex_number_to_hex_hash():
    assert hex_number_to_hex_hash("AABBCC") == "#AABBCC"
    assert hex_number_to_hex_hash("#AABBCC") == "#AABBCC"


def test_hex_number_to_hex_hash_error_wrong_char():
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AABBCX")


def test_hex_number_to_hex_hash_error_wrong_place():
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AA#BCC")


def test_hex_number_to_hex_hash_error_wrong_number():
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AABBCCE")


def test_color_to_hex():
    assert color_to_hex("black") == "#000000"
    assert color_to_hex("navy") == "#000080"
    assert color_to_hex("pink").upper() == "#FFC0CB"
