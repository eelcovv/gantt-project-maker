"""
Definition of CBS rbg colors. Based on the color rgb definitions from the cbs LaTeX template
"""

import logging

import matplotlib as mpl
from matplotlib import colors as mcolors

import webcolors

_logger = logging.getLogger(__name__)

CBS_COLORS_RBG = {
    "corporateblauw": (39, 29, 108),
    "corporatelichtblauw": (0, 161, 205),
    "donkerblauw": (0, 88, 184),
    "donkerblauwvergrijsd": (22, 58, 114),
    "lichtblauw": (0, 161, 205),  # zelfde als corporatelichtblauw
    "lichtblauwvergrijsd": (5, 129, 162),
    "geel": (255, 204, 0),
    "geelvergrijsd": (255, 182, 0),
    "oranje": (243, 146, 0),
    "oranjevergrijsd": (206, 124, 0),
    "rood": (233, 76, 10),
    "roodvergrijsd": (178, 61, 2),
    "roze": (175, 14, 128),
    "rozevergrijsd": (130, 4, 94),
    "grasgroen": (83, 163, 29),
    "grasgroenvergrijsd": (72, 130, 37),
    "appelgroen": (175, 203, 5),
    "appelgroenvergrijsd": (137, 157, 12),
    "violet": (172, 33, 142),
    "highchartslichtgrijs": (239, 239, 239),  # 6.3% zwart, wordt in highcharts gebruikt
    "lichtgrijs": (224, 224, 224),  # 12% zwart
    "grijs": (102, 102, 102),  # 60% zwart
    "logogrijs": (
        146,
        146,
        146,
    ),  # 42% zwart, color van het CBS-logo in het grijze vlak
    "codecolor": (88, 88, 88),
}


def rgb_to_hex(rgb):
    """
    Converteer een tuple met rgb waardes in een hex

    Parameters
    ----------
    rgb: tuple
        tuple met rgb waardes met ints tussen de 0 en 255, bijv. (10, 54, 255)

    Returns
    -------
    str:
        een sting met een hex representatie van de color
    """
    return "#{0:02x}{1:02x}{2:02x}".format(rgb[0], rgb[1], rgb[2]).upper()


CBS_COLORS_HEX = {
    name: rgb_to_hex(rgb_value) for name, rgb_value in CBS_COLORS_RBG.items()
}

# prepend 'cbs:' to all color names to prevent collision
CBS_COLORS = {
    "cbs:" + name: (value[0] / 255, value[1] / 255, value[2] / 255)
    for name, value in CBS_COLORS_RBG.items()
}


def name_to_hex(name: str):
    """Zet de cbs naam om in een hex code."""
    return CBS_COLORS_HEX[name]


def set_cbs_colors():
    # update the matplotlib colors
    mcolors.get_named_colors_mapping().update(CBS_COLORS)


def update_color_palette(reverse=False, offset=0):
    """
    Functie om de color cycle om te draaien en met een off set te laten beginnen

    Parameters
    ----------
    reverse: bool
        inverteer de color set
    offset: int
        Geef een offset
    """
    plot_colors = mpl.rcParams.get("axes.prop_cycle")
    cbs_palette = list(plot_colors.by_key().values())[0]
    if reverse:
        cbs_palette = cbs_palette[-1::-1]
    if offset > 0:
        offset = offset % len(cbs_palette)
        cbs_palette = cbs_palette[offset:] + cbs_palette[:offset]
    cbs_color_cycle = mpl.cycler(color=cbs_palette)
    param = {"axes.prop_cycle": cbs_color_cycle}
    mpl.rcParams.update(param)


def report_colors():
    for name, value in CBS_COLORS.items():
        _logger.info("{:20s}: {}".format(name, value))


def color_to_hex(color: str):
    """Zet de color naam om in een hex code"""
    color_hex_code = None
    if color is not None:
        try:
            color_hex_code = name_to_hex(color)
            _logger.debug(f"color {color} met cbs colors omgezet naar {color_hex_code}")
        except KeyError:
            try:
                color_hex_code = webcolors.name_to_hex(color)
                _logger.debug(
                    f"color {color} met webcolors omgezet naar {color_hex_code}"
                )
            except (AttributeError, ValueError) as err:
                if set(list(color.upper())).difference(set(list("1234567890ABCDEF"))):
                    _logger.warning(f"color {color} wordt niet herkend!")
                else:
                    _logger.debug(f"color {color} geeft {err} error. Zet om in hex")
                color_hex_code = f"#{color}"
    return color_hex_code
