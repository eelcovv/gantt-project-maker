import pytest

from gantt_project_maker.colors import hex_number_to_hex_hash, color_to_hex


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


def hex_number_to_hex_hash_empty_string():
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("")


def hex_number_to_hex_hash_short_hex():
    assert hex_number_to_hex_hash("ABC") == "#AABBCC"


def hex_number_to_hex_hash_lowercase():
    assert hex_number_to_hex_hash("aabbcc") == "#AABBCC"


def color_to_hex_invalid_color():
    with pytest.raises(KeyError):
        color_to_hex("invalidcolor")


def color_to_hex_empty_string():
    with pytest.raises(KeyError):
        color_to_hex("")
