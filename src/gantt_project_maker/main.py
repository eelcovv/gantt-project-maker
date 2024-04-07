"""
This is the main start-up file of the project planner
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
from gantt_project_maker.project_classes import (
    ProjectPlanner,
    SCALES,
    parse_date,
    extend_suffix,
)
from gantt_project_maker.utils import check_if_date

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


############################################################################


def get_info_from_file_or_settings(settings, key):
    """
    Get the information directly from the settings or from a separate file if a filename is given
    Parameters
    ----------
    settings: dict
        Settings file
    key: str
        Key of the settings file we want to read

    Returns
    -------
    dict:
        Structure with information from the settings or separate file

    """
    information = settings[key]

    if isinstance(information, str):
        with codecs.open(information, "r", encoding="UTF-8") as stream:
            information = yaml.load(stream=stream, Loader=yaml.Loader)

    return information


def get_pasted_employees(args_employee, employees_info):
    """get the list of full names or requested employees and return as a comma separated string"""
    all_employees = []
    for employee in args_employee:
        employee_name = get_employee_name(employees_info, employee)
        all_employees.append(employee_name)
    all_employees = ", ".join(all_employees)
    return all_employees


def get_employee_name(employees_info, employee):
    """get the full name of the employee from the settings file"""
    try:
        request_employee = employees_info[employee]
    except KeyError as err:
        _logger.warning(err)
        raise KeyError(
            f"Employee {employee} given via argument is not find in section 'employees' "
            f"in settings file. Please add this employee to your settings"
        )
    else:
        try:
            request_name = request_employee["name"]
        except KeyError as err:
            _logger.warning(err)
            raise KeyError("'name' not given for employee {request_employee} ")

    return request_name


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as a list of strings
          (for example, ``["--help"]``).

    Returns:
      obj:`argparse.Namespace`: command line parameters namespace
    """

    parser = argparse.ArgumentParser(
        description="A front end to the python-gantt project planning"
    )
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
        "-q",
        "--quiet",
        dest="loglevel",
        help="set loglevel to WARNING",
        action="store_const",
        const=logging.WARNING,
    )
    parser.add_argument(
        "-vvv",
        "--very_verbose",
        help="Also show the logging of the gantt module",
        action="store_true",
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
        "--no_details",
        help="Suppress all the tasks with the detail attribute.",
        action="store_false",
        dest="details",
    )
    parser.add_argument(
        "-e",
        "--export_to_xlsx",
        help="Export the project plan to Excel",
        action="append",
        nargs="*",
    )
    parser.add_argument(
        "-c",
        "--collaps_tasks",
        help="Collaps the tasks per project to one task to remove details",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--resources",
        help="Write the resources file of the planning",
        action="store_true",
    )
    parser.add_argument(
        "--vacations",
        help="Write the vacations file of all the  employees",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--employee",
        help="Only use the projects of this employee. Can be given multiple times for multiple "
        "employees.",
        action="append",
    )
    parser.add_argument(
        "-f",
        "--filter_employees",
        help="Only include tasks to which this employee contributes. Can be given multiple times for multiple "
        "employees.",
        action="append",
    )
    parser.add_argument(
        "--projects",
        help="Only include the main project given in this list. Argument can be given multiple times for multiple "
        "projects to include. Alternatively, a comma-separated list of projects may be given. If not given, "
        "all projects defined under 'projects' will be included.",
        action="append",
    )
    parser.add_argument(
        "-p",
        "--period",
        help="On export this period from the list of periods as given in the settings file. If "
        "not given, all the periods are writen to file",
        action="append",
    )
    parser.add_argument(
        "--start_planning",
        type=check_if_date,
        help="Start of the planning. If not given, the value given in de settings file is taken",
    )
    parser.add_argument(
        "--end_planning",
        type=check_if_date,
        help="End of the planning. If not given, the value given in de settings file is taken",
    )
    parser.add_argument(
        "--weeks_margin_left",
        type=int,
        help="Shifts start of planning with this number of weeks left without adding projects. Default is read "
        "from the settings file. This value overrides the default",
    )
    parser.add_argument(
        "--weeks_margin_right",
        type=int,
        help="Shifts start of planning with this number of weeks right without adding projects. Default is read "
        "from the settings file. This value overrides the default.",
    )
    parser.add_argument("--suffix", help="Add a suffix to the final output filename ")
    parser.add_argument("--pdf", help="Save the svg also as pdf ", action="store_true")

    return parser.parse_args(args)


def setup_logging(loglevel: int):
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


def check_if_items_are_available(
    requested_items: list, available_items: dict, label: str = ""
):
    """
    Check is the passed items in the list are available in the keys of the dictionary

    Args:
    requested_items (list): All requested items in the list
    available_items (dict): The dictionary with the keys for which the check is performed
    label (str, optional): Used for information to the screen

    """
    unique_available_items = set(list(available_items.keys()))
    if missing_items := set(requested_items).difference(unique_available_items):
        raise ValueError(
            f"The {label} {missing_items} are not defined in the settings file.\n"
            f"The following keys are available: {unique_available_items}"
        )
    return True


def get_projects_from_arguments(projects_args) -> list or None:
    """
    Get the projects from the command line arguments and return a list

    Args:
        projects_args (list or None): The list of projects may contain comma-separated values

    Returns:
        list or None: The list of projects
    """

    projects = None
    if projects_args is not None:
        projects = list()
        for project in projects_args:
            all_projects = project.split(",")
            projects.extend(all_projects)
    return projects


def make_banner(width=80) -> None:
    """
    Make a banner with the start time
    Args:
        width (int, optional): Width of the banner.
        Defaults to 80
    """
    print("-" * width)
    exe = Path(sys.argv[0]).stem
    now = datetime.now()
    print(
        f"Start '{exe} {' '.join(sys.argv[1:])}'\nat {now.date()} {now.time().strftime('%H:%M')} "
    )
    print("-" * width)


def main(args):
    """Wrapper allowing: func:`postal_code2nuts` to be called with string arguments in a CLI fashion

    Instead of returning the value from: func:`postal_code2nuts`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as a list of strings
          (for example, ``["--verbose", "42"]``).
    """

    args = parse_args(args)

    if args.loglevel < logging.WARNING:
        make_banner()

    setup_logging(args.loglevel)
    if args.very_verbose:
        gantt_logger = logging.getLogger("Gantt")
        gantt_logger.setLevel(args.loglevel)

    _logger.info("Reading settings file {}".format(args.settings_filename))
    with codecs.open(args.settings_filename, "r", encoding="UTF-8") as stream:
        settings = yaml.load(stream=stream, Loader=yaml.Loader)

    general_settings = settings["general"]
    try:
        project_settings_per_project_leader = settings[
            "project_settings_file_per_employee"
        ]
    except KeyError as err:
        _logger.warning(err)
        raise KeyError(
            "Entry project_settings_file_per_employee not found. Are you sure this"
            "is the main settingsfile and not the settings file of an employee?"
        )
    period_info = settings["periods"]
    dayfirst = general_settings["dayfirst"]

    if args.scale is not None:
        scale_key = args.scale
    else:
        scale_key = general_settings.get("scale", "daily")
    scale = SCALES[scale_key]

    if args.start_planning is None:
        start = parse_date(general_settings["planning_start"], dayfirst=dayfirst)
    else:
        start = parse_date(args.start_planning, dayfirst=dayfirst)
    if args.end_planning is None:
        end = parse_date(general_settings["planning_end"], dayfirst=dayfirst)
    else:
        end = parse_date(args.end_planning, dayfirst=dayfirst)

    if args.weeks_margin_left is None:
        weeks_margin_left = general_settings.get("weeks_margin_left")
    else:
        weeks_margin_left = args.weeks_margin_left

    if args.weeks_margin_right is None:
        weeks_margin_right = general_settings.get("weeks_margin_right")
    else:
        weeks_margin_right = args.weeks_margin_right

    programma_title = general_settings["title"]
    programma_color = general_settings.get("color")
    vacation_color = general_settings.get("vacation_color", programma_color)
    output_directories = general_settings.get("output_directories")
    excel_info = settings.get("excel")
    employees_info = get_info_from_file_or_settings(settings=settings, key="employees")
    vacations_info = get_info_from_file_or_settings(settings=settings, key="vacations")

    if args.employee:
        all_employees = get_pasted_employees(
            args.employee, employees_info=employees_info
        )
        programma_title += f"/{all_employees}"

    if args.filter_employees:
        all_filter_employees = get_pasted_employees(
            args.filter_employees, employees_info=employees_info
        )
        programma_title += f": {all_filter_employees}"

    filter_projects = get_projects_from_arguments(args.projects)

    fill = "black"
    stroke = "black"
    stroke_width = 0
    font_family = "Verdana"
    if font_info := general_settings.get("font_info"):
        fill = font_info.get("fill", fill)
        stroke = font_info.get("stroke", stroke)
        stroke_width = font_info.get("stroke_width", stroke_width)
        font_family = font_info.get("font_family", font_family)

    if custom_colors := general_settings.get("custom_colors"):
        set_custom_colors(custom_colors=custom_colors)

    vacations_title_default = "Vacations"
    if country_code := general_settings.get("country_code"):
        locale.setlocale(locale.LC_TIME, country_code)
        if country_code.startswith("nl"):
            vacations_title_default = "Vakanties"
    vacations_title = general_settings.get("vacations_title", vacations_title_default)

    if output_directories is not None:
        planning_directory = Path(output_directories.get("planning", "."))
        resources_directory = Path(output_directories.get("resources", "."))
        excel_directory = Path(output_directories.get("excel", "."))
        vacations_directory = Path(output_directories.get("vacations", "."))
    else:
        planning_directory = Path(".")
        resources_directory = Path(".")
        excel_directory = Path(".")
        vacations_directory = Path(".")

    if args.employee is not None:
        check_if_items_are_available(
            requested_items=args.employee,
            available_items=project_settings_per_project_leader,
            label="employee project",
        )
    if args.filter_employees is not None:
        check_if_items_are_available(
            requested_items=args.filter_employees,
            available_items=employees_info,
            label="employee task",
        )

    if args.period is not None:
        check_if_items_are_available(
            requested_items=args.period, available_items=period_info, label="period"
        )

    # read the settings file per employee
    settings_per_project_leader = {}
    for (
        project_leader_key,
        employee_settings_file,
    ) in project_settings_per_project_leader.items():
        if args.employee is not None and project_leader_key not in args.employee:
            _logger.debug(
                f"Skip reading settings file for employee {project_leader_key}"
            )
            continue

        _logger.info(
            f"Reading settings file {employee_settings_file} of  employee {project_leader_key}"
        )
        with codecs.open(employee_settings_file, encoding="UTF-8") as stream:
            settings_per_project_leader[project_leader_key] = yaml.load(
                stream=stream, Loader=yaml.Loader
            )

    if args.output_filename is None:
        output_filename = Path(args.settings_filename).with_suffix(".svg")
        # add employees from input arguments to output file name
        if args.employee is not None:
            output_filename = extend_suffix(
                output_filename=output_filename, extensions=args.employee
            )

        # add filtered employees from input arguments to output file name
        if args.filter_employees is not None:
            extensions = ["contributors"] + sorted(args.filter_employees)
            output_filename = extend_suffix(
                output_filename=output_filename, extensions=extensions
            )
    else:
        # Treat the output filename as defined on the command line
        output_filename = Path(args.output_filename).with_suffix(".svg")

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
                today = parse_date(today_reference, dayfirst=dayfirst)
                _logger.debug("Setting date to {}".format(today))
        else:
            _logger.debug("today key found be no date defined")

    # Begin de planning
    planning = ProjectPlanner(
        programma_title=programma_title,
        vacations_title=vacations_title,
        programma_color=programma_color,
        vacation_color=vacation_color,
        output_file_name=output_filename,
        planning_start=start,
        planning_end=end,
        weeks_margin_left=weeks_margin_left,
        weeks_margin_right=weeks_margin_right,
        today=today,
        dayfirst=dayfirst,
        scale=scale,
        period_info=period_info,
        excel_info=excel_info,
        details=args.details,
        filter_employees=args.filter_employees,
        save_svg_as_pdf=args.pdf,
        collaps_tasks=args.collaps_tasks,
        periods=args.period,
    )

    # add global information, vacations and employees
    planning.add_global_information(
        fill=fill, stroke=stroke, stroke_width=stroke_width, font_family=font_family
    )
    planning.add_vacations(vacations_info=vacations_info)
    planning.add_employees(employees_info=employees_info)

    # Add the general tasks per employee. It is not mandatory to add tasks_and_milestones,
    # however, you may. The advantage is that multiply tasks can share the same milestone
    for (
        project_leader_key,
        project_leader_settings,
    ) in settings_per_project_leader.items():
        if tasks_and_milestones_info := project_leader_settings.get(
            "tasks_and_milestones"
        ):
            _logger.info(f"Adding global tasks en milestones of {project_leader_key} ")
            variables_info = project_leader_settings.get("variables")
            planning.add_tasks_and_milestones(
                tasks_and_milestones_info=tasks_and_milestones_info,
                variables_info=variables_info,
            )

    # Voeg nu de projecten per employee toe.
    for (
        project_leader_key,
        project_leader_settings,
    ) in settings_per_project_leader.items():
        if args.employee is not None and project_leader_key not in args.employee:
            _logger.debug(f"Skip employee {project_leader_key}")
            continue

        project_employee_info = project_leader_settings["general"]
        subprojects_info = project_leader_settings["projects"]
        variables_info = project_leader_settings.get("variables")

        subprojects_selection = project_employee_info["projects"]
        subprojects_title = project_employee_info["title"]
        subprojects_color = project_employee_info.get("color")
        if filter_projects is not None:
            # in case a project is given on the command line argument, only allow projects given on the filter.
            subprojects_selection = list(
                set(subprojects_selection).intersection(set(filter_projects))
            )
        if subprojects_selection:
            planning.make_projects(
                project_leader_key=project_leader_key,
                subprojects_info=subprojects_info,
                subprojects_selection=subprojects_selection,
                subprojects_title=subprojects_title,
                subprojects_color=subprojects_color,
                variables_info=variables_info,
            )

    # Everything has been added to the planning. Write it to file
    planning.write_planning(
        write_resources=args.resources,
        write_vacations=args.vacations,
        planning_output_directory=planning_directory,
        resource_output_directory=resources_directory,
        vacations_output_directory=vacations_directory,
        periods=args.period,
        suffix=args.suffix,
    )

    planning.make_resource_dataframe()

    if args.export_to_xlsx is not None:
        if args.export_to_xlsx[0]:
            excel_output_formats = [out for out in args.export_to_xlsx[0]]
        else:
            excel_output_formats = ["all"]
        planning.export_to_excel(
            excel_output_directory=excel_directory,
            excel_output_formats=excel_output_formats,
        )


def run():
    """Calls: func:`main` passing the CLI arguments extracted from: obj:`sys.argv`

    This function can be used as an entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^ This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m gantt_projectplanner.skeleton 42
    #
    run()
