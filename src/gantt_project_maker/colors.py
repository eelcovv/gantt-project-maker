"""
Definition of CBS rbg colors. Based on the color rgb definitions from the cbs LaTeX template
"""

import logging

import webcolors

_logger = logging.getLogger(__name__)


# A bit tricky, but we use it to store the custom colors
CUSTOM_COLORS_HEX = {}


def hex_number_to_hex_hash(hex_number):
    """
    Args:
        hex_number: int or str
            Hexadecimal representation of a color, with or without a leading #

    Returns: str
        Hexadecimal color with a leading #
    """
    hex_code = str(hex_number)
    if set(list(hex_code.upper())).difference(set(list("1234567890ABCDEF#"))):
        raise ValueError(
            f"Hex color {hex_code} is not valid as it contains characters out of the valid range"
        )
    if not hex_code.startswith("#"):
        if "#" in hex_code:
            raise ValueError(
                f"Hex color {hex_code} is not valid as the # is not at the start"
            )
        hex_code = f"#{hex_code}"
    if len(hex_code) != 7:
        raise ValueError(
            f"Hex color {hex_code} is not valid as is has an invalid amount of digit "
        )
    return hex_code


def set_custom_colors(custom_colors):
    """Set the hex colors defined in the dictionary to the global variable CUSTOM_COLORS_HEX"""
    for color_name, color_hex in custom_colors.items():
        CUSTOM_COLORS_HEX[color_name] = hex_number_to_hex_hash(color_hex)


def color_to_hex(color: str):
    """Convert a named color into a hex code with a leading #"""
    color_hex_code = None
    if color is not None:
        try:
            color_hex_code = CUSTOM_COLORS_HEX[color]
            _logger.debug(f"color {color} met cbs colors omgezet naar {color_hex_code}")
        except KeyError:
            try:
                color_hex_code = webcolors.name_to_hex(color)
                _logger.debug(
                    f"color {color} met webcolors omgezet naar {color_hex_code}"
                )
            except (AttributeError, ValueError) as err:
                color_hex_code = hex_number_to_hex_hash(color)

    return color_hex_code
