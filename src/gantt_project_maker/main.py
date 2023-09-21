"""
This is the main start up file of the project planner
"""

import argparse
import codecs
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from gantt_projectplanner import __version__
from gantt_projectplanner.project_classes import ProjectPlanner, SCALES, parse_date

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


############################################################################


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument("settings_filename", help="Name of the configuration file")
    parser.add_argument(
        "--test",
        help="Only do what you want to do, do not write to file",
        default=False,
        action="store_true",
    )
    parser.add_argument("--output_filename", help="Name of the text output file")
    parser.add_argument(
        "--version",
        action="version",
        version=f"gantt_projectplanner {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
        default=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--debug",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "-s",
        "--scale",
        help="Kies de schaal van het grid van het schema",
        choices=set(SCALES.keys()),
    )
    parser.add_argument(
        "--details",
        help="Voer ook de detailtaken uit.",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--geen_details",
        help="Onderdruk alle detailtaken voor het grote overzicht.",
        action="store_false",
        dest="details",
    )
    parser.add_argument(
        "-e",
        "--export_to_xlsx",
        help="Exporteer de planning naar excel",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--bronnen",
        help="Schrijf ook de bronnen file de planning naar excel",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--medewerker",
        help="Neem alleen de medewerkers mee die  opgegeven zijn. Kan meerdere keren gegeven worden voor meerdere "
        "medewerkers",
        action="append",
    )
    parser.add_argument(
        "-p",
        "--periode",
        help="Neem alleen de periode mee die  opgegeven is. Kan meerdere keren gegeven worden voor meerdere "
        "periodes. Als niets gegeven wordt dan nemen we ze allemaal",
        action="append",
    )

    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    if loglevel == logging.DEBUG:
        log_format = "[%(levelname)5s]:%(filename)s/%(lineno)d: %(message)s"
    else:
        log_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(
        level=loglevel,
        stream=sys.stdout,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def check_beschikbaar(gevraagd, beschikbaar, label=""):
    """
    Check of de meegegeven selectie van keys in 'gevraagd' wel terug te vinden is in de keys van 'beschikbaar'

    Parameters
    ----------
    gevraagd: list
        Items die gevraagd worden
    beschikbaar: dict
        Dictionary met keys die beschikbaar moeten zijn
    label: str
        Alleen ter informatie bij het schrijven naar scherm als label

    """
    beschikbare_items = set(list(beschikbaar.keys()))
    if missende_items := set(gevraagd).difference(beschikbare_items):
        raise ValueError(
            f"De {label} {missende_items} is niet in de settings file gedefinieerd.\n"
            f"Beschikbaar zijn {beschikbare_items}"
        )


def main(args):
    args = parse_args(args)
    print("-" * 80)
    exe = Path(sys.argv[0]).stem
    now = datetime.now()
    print(
        f"Start '{exe} {' '.join(sys.argv[1:])}' om {now.date()} {now.time().strftime('%H:%M')} "
    )
    print("-" * 80)

    setup_logging(args.loglevel)

    _logger.info("Reading settings file {}".format(args.settings_filename))
    with codecs.open(args.settings_filename, "r", encoding="UTF-8") as stream:
        settings = yaml.load(stream=stream, Loader=yaml.Loader)

    general_settings = settings["algemeen"]
    periode_info = settings["periodes"]

    if args.scale is not None:
        scale_key = args.scale
    else:
        scale_key = general_settings.get("scale", "daily")
    scale = SCALES[scale_key]

    start = parse_date(general_settings["planning_start"])
    einde = parse_date(general_settings["planning_einde"])
    programma_titel = general_settings["titel"]
    programma_kleur = general_settings.get("kleur")
    output_directories = general_settings.get("output_directories")
    project_settings_per_medewerker = settings["project_settings_file_per_medewerker"]

    if output_directories is not None:
        planning_directory = Path(output_directories.get("planning", "."))
        resources_directory = Path(output_directories.get("bronnen", "."))
        excel_directory = Path(output_directories.get("excel", "."))
    else:
        planning_directory = Path(".")
        resources_directory = Path(".")
        excel_directory = Path(".")

    if args.medewerker is not None:
        check_beschikbaar(
            gevraagd=args.medewerker,
            beschikbaar=project_settings_per_medewerker,
            label="medewerker",
        )

    if args.periode is not None:
        check_beschikbaar(
            gevraagd=args.periode, beschikbaar=periode_info, label="periode"
        )

    vakanties_info = settings.get("vakanties")
    medewerkers_info = settings.get("medewerkers")
    excel_info = settings.get("excel")

    # lees de settings file per medewerk
    settings_per_medewerker = {}
    for (
        medewerker_key,
        medewerker_settings_file,
    ) in project_settings_per_medewerker.items():
        _logger.info(
            f"Van medewerker {medewerker_key} lees settings file  {medewerker_settings_file}"
        )
        with codecs.open(medewerker_settings_file, "r", encoding="UTF-8") as stream:
            settings_per_medewerker[medewerker_key] = yaml.load(
                stream=stream, Loader=yaml.Loader
            )

    if args.output_filename is None:
        output_filename = Path(args.settings_filename).with_suffix(".svg")
    else:
        output_filename = Path(args.output_filename).with_suffix(".svg")

    if args.medewerker is not None:
        output_filename = Path(
            "_".join([output_filename.with_suffix("").as_posix()] + args.medewerker)
        ).with_suffix(".svg")

    today = None
    try:
        today_reference = general_settings["referentie_datum"]
    except KeyError:
        _logger.debug("No date found")
    else:
        if today_reference is not None:
            if today_reference == "vandaag":
                today = datetime.today().date()
                _logger.debug("Setting date to today {}".format(today))
            else:
                today = parse_date(today_reference)
                _logger.debug("Setting date to {}".format(today))
        else:
            _logger.debug("today key found be no date defined")

    # Begin de planning
    planning = ProjectPlanner(
        programma_titel=programma_titel,
        programma_kleur=programma_kleur,
        output_file_name=output_filename,
        planning_start=start,
        planning_einde=einde,
        vandaag=today,
        schaal=scale,
        periode_info=periode_info,
        excel_info=excel_info,
        details=args.details,
    )

    # voeg globale informatie, vakanties en medewerkers toe
    planning.maak_globale_informatie()
    planning.maak_vakanties(vakanties_info=vakanties_info)
    planning.maak_medewerkers(medewerkers_info=medewerkers_info)

    # Voeg nu de algemene taken per medewerker toe. Het is niet verplicht taken_en_mijlpalen op te geven,
    # maar kan wel. Het voordeel is dat taken tussen medewerkers gedeeld kunnen worden
    for (
        medewerker_key,
        medewerker_settings,
    ) in settings_per_medewerker.items():
        if taken_en_mijlpalen_info := medewerker_settings.get("taken_en_mijlpalen"):
            _logger.info(f"Voegen globale taken en mijlpalen van {medewerker_key} toe")
            planning.maak_taken_en_mijlpalen(
                taken_en_mijlpalen_info=taken_en_mijlpalen_info
            )

    # Voeg nu de projecten per medewerker toe.
    for (
        medewerker_key,
        medewerker_settings,
    ) in settings_per_medewerker.items():
        if args.medewerker is not None and medewerker_key not in args.medewerker:
            _logger.debug(f"Medewerker {medewerker_key} wordt over geslagen")
            continue

        project_medewerker_info = medewerker_settings["algemeen"]
        subprojecten_info = medewerker_settings["projecten"]

        subprojecten_selectie = project_medewerker_info["projecten"]
        subprojecten_titel = project_medewerker_info["titel"]
        subprojecten_kleur = project_medewerker_info.get("kleur")
        planning.maak_projecten(
            subprojecten_info=subprojecten_info,
            subprojecten_selectie=subprojecten_selectie,
            subprojecten_titel=subprojecten_titel,
            subprojecten_kleur=subprojecten_kleur,
        )

    # Alles is aan de planning toegevoegd. Schrijf hem nu naar svg en eventueel naar excel
    planning.schrijf_planning(
        schrijf_bronnen=args.bronnen,
        planning_output_directory=planning_directory,
        resource_output_directory=resources_directory,
        periodes=args.periode,
    )

    if args.export_to_xlsx:
        planning.exporteer_naar_excel(excel_output_directory=excel_directory)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m gantt_projectplanner.skeleton 42
    #
    run()
