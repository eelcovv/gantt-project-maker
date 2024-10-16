import pytest

from gantt_project_maker.colors import hex_number_to_hex_hash, color_to_hex


def test_hex_number_to_hex_hash():
    """
    Test that hex_number_to_hex_hash correctly formats a hex color string.
    """
    assert hex_number_to_hex_hash("AABBCC") == "#AABBCC"
    assert hex_number_to_hex_hash("#AABBCC") == "#AABBCC"


def test_hex_number_to_hex_hash_error_wrong_char():
    """
    Test that hex_number_to_hex_hash raises a ValueError for invalid characters.
    """
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AABBCX")


def test_hex_number_to_hex_hash_error_wrong_place():
    """
    Test that hex_number_to_hex_hash raises a ValueError for misplaced hash symbol.
    """
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AA#BCC")


def test_hex_number_to_hex_hash_error_wrong_number():
    """
    Test that hex_number_to_hex_hash raises a ValueError for incorrect length.
    """
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("AABBCCE")


def test_color_to_hex():
    """
    Test that color_to_hex correctly converts color names to hex values.
    """
    assert color_to_hex("black") == "#000000"
    assert color_to_hex("navy") == "#000080"
    assert color_to_hex("pink").upper() == "#FFC0CB"


def hex_number_to_hex_hash_empty_string():
    """
    Test that hex_number_to_hex_hash raises a ValueError for an empty string.
    """
    with pytest.raises(ValueError):
        hex_number_to_hex_hash("")


def hex_number_to_hex_hash_short_hex():
    """
    Test that hex_number_to_hex_hash correctly formats a short hex color string.
    """
    assert hex_number_to_hex_hash("ABC") == "#AABBCC"


def hex_number_to_hex_hash_lowercase():
    """
    Test that hex_number_to_hex_hash correctly formats a lowercase hex color string.
    """
    assert hex_number_to_hex_hash("aabbcc") == "#AABBCC"


def color_to_hex_invalid_color():
    """
    Test that color_to_hex raises a KeyError for an invalid color name.
    """
    with pytest.raises(KeyError):
        color_to_hex("invalidcolor")


def color_to_hex_empty_string():
    """
    Test that color_to_hex raises a KeyError for an empty string.
    """
    with pytest.raises(KeyError):
        color_to_hex("")
