"""
This is the main start up file of the project planner
"""

import argparse
import codecs
import locale
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from gantt_project_maker import __version__
from gantt_project_maker.colors import set_custom_colors
from gantt_project_maker.project_classes import ProjectPlanner, SCALES, parse_date

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
    parser.add_argument("--output_filename", help="Name of the text output file")
    parser.add_argument(
        "--version",
        action="version",
        version=f"gantt_project_maker {__version__}",
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
        help="The scale of the grid of the project scheme",
        choices=set(SCALES.keys()),
    )
    parser.add_argument(
        "--details",
        help="Add all the tasks with the detail attribute",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--geen_details",
        help="Suppress all the tasks with the detail attribute.",
        action="store_false",
        dest="details",
    )
    parser.add_argument(
        "-e",
        "--export_to_xlsx",
        help="Export the project plan to Excel",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--resources",
        help="Write the resources file of the planning",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--employee",
        help="Only use the projects of this employee. Can be given multiple times for multiple employees"
        "employees",
        action="append",
    )
    parser.add_argument(
        "-p",
        "--period",
        help="On export this period from the list of periods as given in the settings file. If not given, all"
        "the periods are writen to file",
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


def check_if_items_are_available(requested_items, available_items, label=""):
    """
    Check is the passed items in the list are available in the keys of the dictionary

    Parameters
    ----------
    requested_items: list
        All requested items  in the list
    available_items: dict
        The dictionary with the keys
    label: str
        Used for information to the screen

    """
    unique_available_items = set(list(available_items.keys()))
    if missing_items := set(requested_items).difference(unique_available_items):
        raise ValueError(
            f"The {label} {missing_items} are not defined in the settings file.\n"
            f"The following keys are available: {unique_available_items}"
        )
    return True


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

    general_settings = settings["general"]
    period_info = settings["periods"]

    if args.scale is not None:
        scale_key = args.scale
    else:
        scale_key = general_settings.get("scale", "daily")
    scale = SCALES[scale_key]

    start = parse_date(general_settings["planning_start"])
    end = parse_date(general_settings["planning_end"])
    programma_title = general_settings["title"]
    programma_color = general_settings.get("color")
    output_directories = general_settings.get("output_directories")
    project_settings_per_employee = settings["project_settings_file_per_employee"]

    if custom_colors := general_settings.get("custom_colors"):
        set_custom_colors(custom_colors=custom_colors)
    if country_code := general_settings.get("country_code"):
        locale.setlocale(locale.LC_TIME, country_code)

    if output_directories is not None:
        planning_directory = Path(output_directories.get("planning", "."))
        resources_directory = Path(output_directories.get("resources", "."))
        excel_directory = Path(output_directories.get("excel", "."))
    else:
        planning_directory = Path(".")
        resources_directory = Path(".")
        excel_directory = Path(".")

    if args.employee is not None:
        check_if_items_are_available(
            requested_items=args.employee,
            available_items=project_settings_per_employee,
            label="employee",
        )

    if args.period is not None:
        check_if_items_are_available(
            requested_items=args.period, available_items=period_info, label="period"
        )

    vacations_info = settings.get("vacations")
    employees_info = settings.get("employees")
    excel_info = settings.get("excel")

    # lees de settings file per medewerk
    settings_per_employee = {}
    for (
        employee_key,
        employee_settings_file,
    ) in project_settings_per_employee.items():
        _logger.info(
            f"Reading settings file {employee_settings_file} of  employee {employee_key}"
        )
        with codecs.open(employee_settings_file, "r", encoding="UTF-8") as stream:
            settings_per_employee[employee_key] = yaml.load(
                stream=stream, Loader=yaml.Loader
            )

    if args.output_filename is None:
        output_filename = Path(args.settings_filename).with_suffix(".svg")
    else:
        output_filename = Path(args.output_filename).with_suffix(".svg")

    if args.employee is not None:
        output_filename = Path(
            "_".join([output_filename.with_suffix("").as_posix()] + args.employee)
        ).with_suffix(".svg")

    today = None
    try:
        today_reference = general_settings["reference_date"]
    except KeyError:
        _logger.debug("No date found")
    else:
        if today_reference is not None:
            if today_reference == "today":
                today = datetime.today().date()
                _logger.debug("Setting date to today {}".format(today))
            else:
                today = parse_date(today_reference)
                _logger.debug("Setting date to {}".format(today))
        else:
            _logger.debug("today key found be no date defined")

    # Begin de planning
    planning = ProjectPlanner(
        programma_title=programma_title,
        programma_color=programma_color,
        output_file_name=output_filename,
        planning_start=start,
        planning_end=end,
        today=today,
        scale=scale,
        period_info=period_info,
        excel_info=excel_info,
        details=args.details,
    )

    # voeg globale informatie, vacations en employees toe
    planning.add_global_information()
    planning.add_vacations(vacations_info=vacations_info)
    planning.add_employees(employees_info=employees_info)

    # Voeg nu de algemene tasks per employee toe. Het is niet verplicht tasks_and_milestones op te geven,
    # maar kan wel. Het voordeel is dat tasks tussen employees gedeeld kunnen worden
    for (
        employee_key,
        employee_settings,
    ) in settings_per_employee.items():
        if tasks_and_milestones_info := employee_settings.get("tasks_and_milestones"):
            _logger.info(f"Adding global tasks en milestones of {employee_key} ")
            planning.add_tasks_and_milestones(
                tasks_and_milestones_info=tasks_and_milestones_info
            )

    # Voeg nu de projecten per employee toe.
    for (
        employee_key,
        employee_settings,
    ) in settings_per_employee.items():
        if args.employee is not None and employee_key not in args.employee:
            _logger.debug(f"Skip employee {employee_key}")
            continue

        project_employee_info = employee_settings["general"]
        subprojects_info = employee_settings["projects"]

        subprojects_selection = project_employee_info["projects"]
        subprojects_title = project_employee_info["title"]
        subprojects_color = project_employee_info.get("color")
        planning.make_projects(
            subprojects_info=subprojects_info,
            subprojects_selection=subprojects_selection,
            subprojects_title=subprojects_title,
            subprojects_color=subprojects_color,
        )

    # Alles is aan de planning toegevoegd. Schrijf hem nu naar svg en eventueel naar excel
    planning.write_planning(
        write_resources=args.resources,
        planning_output_directory=planning_directory,
        resource_output_directory=resources_directory,
        periods=args.period,
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
