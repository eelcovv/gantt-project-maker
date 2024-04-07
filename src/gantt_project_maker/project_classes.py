"""
Class files for the gantt-project-maker project
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Union

import dateutil.parser as dparse
import pandas as pd
from dateutil.parser import ParserError
from pandas import DataFrame

import gantt_project_maker.gantt as gantt
from gantt_project_maker.colors import color_to_hex
from gantt_project_maker.excelwriter import (
    write_project_to_excel,
    write_value_to_named_cell,
)
from gantt_project_maker.utils import get_task_contribution, deep_copy_dict

SCALES = dict(
    daily=gantt.DRAW_WITH_DAILY_SCALE,
    weekly=gantt.DRAW_WITH_WEEKLY_SCALE,
    monthly=gantt.DRAW_WITH_MONTHLY_SCALE,
    quarterly=gantt.DRAW_WITH_QUARTERLY_SCALE,
)

EXCEL_TYPES = ["all", "leaders", "contributors"]

_logger = logging.getLogger(__name__)


def insert_variables(line: str, variables_info: dict = None):
    """
    Replace variables inserted as {{ variable_name }} in line by the variables defined in variable_ifo

    Args:
        line (str): Line to replace the variables with
        variables_info (dict, optional): variables to replace. Defaults to None, which leaves the whole line intact

    Returns:
        str: Line with variables replaced
    """

    if variables_info is not None:
        for variable_key, variable_value in variables_info.items():
            search_pattern = "{{\s+" + variable_key + "\s+}}"
            line = re.sub(search_pattern, str(variable_value), line)

    return line


def get_nearest_saturday(date):
    """
    Get the nearest Saturday with respect to 'date'

    Parameters
    ----------
    date: datetime.date
        The reference date

    Returns
    -------
    datetime.date
        Nearest Saturday with respect to the reference date

    """
    d = date.toordinal()
    last = d - 6
    sunday = last - (last % 7)
    saturday = sunday + 6
    if d - saturday > 7 / 2:
        # de afstand tot vorige zaterdag is meer dan een halve week, dus de volgende zaterdag is dichter bij
        saturday += 7
    return date.fromordinal(saturday)


def parse_date(
    date_in: Union[str, datetime], date_default: str = None, dayfirst=False
) -> datetime.date:
    """
    Lees de date_string en parse de datum

    Parameters
    ----------
    date_in: str
        Datum representatie
    date_default:
        Als de date_string None is deze default waarde genomen.
    dayfirst: bool
        Set the day first, e.g. 25-12-2023

    Returns
    -------
    datetime.date():
        Datum
    """
    if date_in is not None:
        try:
            date_out = dparse.parse(date_in.strip(), dayfirst=dayfirst).date()
        except AttributeError:
            # assume the date string is given as a datetime already
            date_out = date_in
    elif date_default is not None and isinstance(date_default, str):
        date_out = dparse.parse(date_default.strip(), dayfirst=dayfirst).date()
    else:
        date_out = date_default
    return date_out


def add_vacation_employee(employee: gantt.Resource, vacations: dict) -> dict:
    """
    Add the vacations of an employee

    Parameters
    ----------
    employee: Resource
        The employee for who you want to add the vacation
    vacations: dict
        A dictionary with items per vacation. Per vacation, you need a start and an end

    Returns
    -------
    dict:
        Dictionary with the vacations.
    """
    vacation_objects = dict()

    if vacations is not None:
        for vacation_key, vacation_properties in vacations.items():
            vacation_objects[vacation_key] = Vacation(
                vacation_properties["start"],
                vacation_properties.get("end"),
                employee=employee,
            )
    return vacation_objects


class StartEndBase:
    """
    Basis van alle classes met een begin- en einddatum.
    """

    def __init__(
        self, start: str, end: str = None, dayfirst=False, variables_info=None
    ):
        """
        Store the dates as date/time objects

        Args:
        start (str): Start date is mandatory
        end (str or None): End date is optional
        dayfirst (bool): Use date with date first
        variables_info (dict, optional):  replace variables in date end and start
        """
        self.variables_info = variables_info
        self.start = parse_date(
            insert_variables(start, variables_info), dayfirst=dayfirst
        )
        self.end = parse_date(insert_variables(end, variables_info), dayfirst=dayfirst)


class Vacation(StartEndBase):
    def __init__(self, start, end=None, employee=None, dayfirst=False):
        super().__init__(start, end, dayfirst=dayfirst)

        if employee is None:
            self.pool = gantt
        else:
            self.pool = employee

        self.add_vacation()

    def add_vacation(self):
        """
        Add common or employee vacations
        """
        self.pool.add_vacations(self.start, self.end)


class EmployeesContributingToTask:
    """
    Class holding all employees attached to a task with the number of hours

    Attributes:
        resources (dict): all the gantt.Resources object
        hours (dict): All the hours per resource working on this taks
    """

    def __init__(self):
        self.resources = dict()
        self.hours = dict()

    def add_resource(self, employee, resource, hours=None):
        """
        Add a resource to the list.

        Args:
            employee (str): Key of the employee to add
            resource (Resource): resource to add
            hours (float): number of hours to add

        """
        self.resources[employee] = resource
        self.hours[employee] = hours

    def get_resources(self):
        """
        Retrieve a list of all the resources working on this task

        Returns:
            list of resources
        """
        return list(self.resources.values())


class Employee:
    """
    Class holding information about one employee

    Args:
        label (str): Label of the employee
        full_name (str, optional): Full name of the employee
        vacations (dict, optional) : Dictionary of the vacations. Defaults to None
        color (str): Color of the employee
    """

    def __init__(
        self,
        label: str,
        full_name: str = None,
        vacations: dict = None,
        color: str = None,
    ):
        """
        Class constructor
        """
        self.label = label
        self.full_name = full_name
        self.color = color
        self.resource = gantt.Resource(name=label, fullname=full_name, color=color)

        if vacations is not None:
            self.vacations = add_vacation_employee(
                employee=self.resource, vacations=vacations
            )
        else:
            self.vacations = None


class BasicElement(StartEndBase):
    def __init__(
        self,
        label,
        project_leader_key=None,
        start=None,
        dependent_of=None,
        color=None,
        project_color=None,
        detail=False,
        display=True,
        dayfirst=False,
        variables_info=None,
        parent=None,
    ):
        super().__init__(start, start, dayfirst, variables_info)
        if label is None:
            raise ValueError("Every task should have a label!")
        self.label = label
        self.project_leader_key = project_leader_key
        self.detail = detail
        self.dependent_of = dependent_of
        self.color = color_to_hex(color)
        self.project_color = color_to_hex(project_color)
        self.display = display
        self.parent = parent


class ProjectTask(BasicElement):
    def __init__(
        self,
        label,
        project_leader_key=None,
        start=None,
        end=None,
        duration=None,
        employees=None,
        dependent_of=None,
        color=None,
        project_color=None,
        detail=False,
        display=True,
        dayfirst=True,
        variables_info=None,
        parent=None,
    ):
        super().__init__(
            label=label,
            project_leader_key=project_leader_key,
            start=start,
            dependent_of=dependent_of,
            color=color,
            project_color=project_color,
            detail=detail,
            display=display,
            dayfirst=dayfirst,
            variables_info=variables_info,
            parent=parent,
        )
        self.end = parse_date(end, dayfirst=dayfirst)
        self.duration = duration
        if self.end is None and self.duration is None:
            msg = (
                f"For a Task, next to a start date, either a end date or a duration needs to be specified. "
                f"None is given for task '{label}'"
            )
            raise ValueError(msg)
        if self.end is not None:
            if self.end < self.start:
                msg = f"End date {self.end} is before {self.start} for Task '{label}'. Please fix this"
                raise ValueError(msg)
        self.employees = employees

        self.element = self.add_task()

    def add_task(self) -> gantt.Task:
        """
        Add a task to the gantt charts
        Returns:
            Task to add the task to the gantt charts

        """
        if self.color is None:
            self.color = self.project_color
        if self.employees is None:
            resources = None
        else:
            resources = self.employees.get_resources()
        task = gantt.Task(
            name=self.label,
            start=self.start,
            stop=self.end,
            duration=self.duration,
            depends_of=self.dependent_of,
            resources=resources,
            color=self.color,
            owner=self.project_leader_key,
            parent=self.parent,
        )
        return task


class ProjectMileStone(BasicElement):
    def __init__(
        self,
        label,
        project_leader_key=None,
        start=None,
        dependent_of=None,
        color=None,
        project_color=None,
        detail=False,
        display=True,
        dayfirst=True,
        variables_info=None,
        parent=None,
    ):
        super().__init__(
            label=label,
            project_leader_key=project_leader_key,
            start=start,
            dependent_of=dependent_of,
            color=color,
            project_color=project_color,
            detail=detail,
            display=display,
            dayfirst=dayfirst,
            variables_info=variables_info,
            parent=parent,
        )

        self.element = self.add_milestone()

    def add_milestone(self) -> gantt.Milestone:
        """
        Create a Milestone and add it to the planning

        Returns:
            ProjectMileStone: Milestone of this project

        """
        element = gantt.Milestone(
            name=self.label,
            start=self.start,
            depends_of=self.dependent_of,
            color=self.color,
            parent=self.parent,
        )
        return element


class ProjectPlanner:
    """
    ProjectPlanner is  class to handle the project planning and generate the output

    Args:
        programma_title (str, optional): Main titel of the whole project
        vacations_title (str, optional): Title of the vacations project
        programma_color (str, optional): First color of the bar
        output_file_name (str, optional): Base name of the output files
        planning_start (datetime, optional): Start of the program
        planning_end (datetime, optional): End of the program
        weeks_margin_left (int, optional): Shift the end of the planning so many weeks to the left without adding
            projects
        weeks_margin_right (int, optional): Shift the end of the planning so many weeks to the right without
            adding projects
        today (datetime, optional): Today's date
        dayfirst (bool, optional): Parse date with the day first. Defaults to False
        scale (str, optional): Which scale is used for the output
        period_info (dict, optional): Information on the periods output
        excel_info (dict, optional): Information on the Excel output
        details (bool, optional): If true, include the details to the programs
        filter_employees (list, optional): If not None, only add task to which  employees in this list contribute

    Attributes:
        tasks_per_resource (DataFrame): Dataframe with tasks per resource

    """

    def __init__(
        self,
        programma_title: str = None,
        vacations_title: str = None,
        programma_color: str = None,
        vacation_color: str = None,
        output_file_name: Path = None,
        planning_start: datetime = None,
        planning_end: datetime = None,
        weeks_margin_left: int = None,
        weeks_margin_right: int = None,
        today: datetime = None,
        dayfirst: bool = False,
        scale: str = None,
        period_info: dict = None,
        excel_info: dict = None,
        details: bool = None,
        filter_employees: list = None,
        save_svg_as_pdf: bool = False,
        collaps_tasks: bool = False,
        periods: list = None,
        tasks_id: str = "task",
        employee_id: str = "employee",
        owner_id: str = "owner",
        contributor_id: str = "contributor",
    ):
        """
        Constructor of the class
        """
        self.tasks_id = tasks_id
        self.employee_id = employee_id
        self.owner_id = owner_id
        self.contributor_id = contributor_id

        self.period_info = period_info
        self.planning_start = planning_start
        self.planning_end = planning_end
        self.date_today = today
        self.dayfirst = dayfirst
        self.scale = scale
        self.details = details
        self.save_svg_as_pdf = save_svg_as_pdf
        self.collaps_tasks = collaps_tasks
        if filter_employees:
            # if filter_employees are given, add them as a set
            self.filter_employees = set(filter_employees)
        else:
            self.filter_employees = None

        self.weeks_margin_left = weeks_margin_left
        self.weeks_margin_right = weeks_margin_right

        self.start_date = planning_start
        self.end_date = planning_end

        if periods is not None:
            for period_key, period_value in period_info.items():
                if period_key in periods:
                    period_start = parse_date(
                        period_value.get("planning_start", self.planning_start)
                    )
                    period_end = parse_date(
                        period_value.get("planning_end", self.planning_end)
                    )
                    if period_start > self.start_date:
                        self.start_date = period_start
                    if period_end < self.end_date:
                        self.end_date = period_end

        self.excel_info = excel_info

        if output_file_name is None:
            self.output_file_name = Path("gantt_projects.svg")
        else:
            self.output_file_name = Path(output_file_name)

        # Make the main project
        self.program = gantt.Project(
            name=programma_title, color=color_to_hex(programma_color)
        )

        # Make the project to store all the vacations
        self.vacations_gantt = gantt.Project(
            name=vacations_title, color=color_to_hex(vacation_color)
        )

        self.project_tasks = dict()
        self.vacations = dict()
        self.employees = dict()
        self.tasks_and_milestones = dict()
        self.subprojects = dict()

        self.tasks_per_resource: Union[DataFrame, None] = None

    @staticmethod
    def add_global_information(
        fill="black", stroke="black", stroke_width=0, font_family="Verdana"
    ):
        """
        Set global pen properties

        Args:
            fill (str, optional): The fill color. Defaults to 'black'.
            stroke (str, optional):  The stroke color. Defaults to 'black'
            stroke_width (int, optional): The stroke width. Defaults to 0
            font_family (str, optional): The font type. Defaults to 'Verdana'
        """
        gantt.define_font_attributes(
            fill=fill, stroke=stroke, stroke_width=stroke_width, font_family=font_family
        )

    def export_to_excel(
        self, excel_output_directory: Path, excel_output_formats: Union[list, None] = None
    ) -> None:
        """
        Write planning to an Excel file

        Args:
            excel_output_directory(Path): Output directory of the Excel files
            excel_output_formats (list): List of Excel files to export as defined in the settings file.
        """

        if self.excel_info is None:
            _logger.warning(
                "Cannot write excel! Please add Excel info to your settings file"
            )
        else:
            excel_output_directory.mkdir(exist_ok=True)
            excel_file = excel_output_directory / self.output_file_name.with_suffix(
                ".xlsx"
            )

            for excel_key, excel_properties in self.excel_info.items():
                if excel_key in excel_output_formats or "all" in excel_output_formats:
                    excel_properties["do_it"] = True
                else:
                    excel_properties["do_it"] = False

            for excel_key, excel_properties in self.excel_info.items():
                if not excel_properties.get("do_it", True):
                    continue

                file_name = extend_suffix(excel_file, excel_key)

                excel_type = excel_properties["type"]

                if excel_type == "leaders":
                    _logger.info(
                        f"Exporting planning to {file_name} for project leaders"
                    )
                    self.write_excel_for_leaders(
                        excel_file=file_name,
                        header_info=excel_properties["header"],
                        column_widths=excel_properties.get("column_widths"),
                    )
                elif excel_type == "contributors":
                    _logger.info(f"Exporting planning to {file_name} for contributors")
                    self.write_excel_for_contributors(
                        excel_file=file_name,
                        header_info=excel_properties["header"],
                        summation_info=excel_properties.get("summations"),
                        column_widths=excel_properties.get("column_widths"),
                    )
                else:
                    msg = f"Unrecognized value for type '{excel_type}'. Please pick from {EXCEL_TYPES}. Skipping"
                    _logger.warning(msg)

    def write_excel_for_leaders(self, excel_file, header_info, column_widths):
        """
        A writer for the project plan of all employees, one sheet per employee

        Args:
            excel_file (Path):  The filename of the Excel file
            header_info (dict):  Information about the header of the Excel file
            column_widths (dict): Fix width of specified columns

        Returns:

        """
        _logger.debug(f"Writing to {excel_file} for leaders")
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            try:
                projects_per_employee = self.program.tasks
            except AttributeError as err:
                raise AttributeError(
                    f"{err}\nproject heeft helemaal geen tasks. Hier gaat what fout"
                )
            else:
                for projecten_employee in projects_per_employee:
                    row_index, level, total_hours = write_project_to_excel(
                        project=projecten_employee,
                        writer=writer,
                        sheet_name=projecten_employee.name,
                        header_info=header_info,
                        column_widths=column_widths,
                    )
                    _logger.debug(
                        f"Wrote project with row: {row_index} level: {level} and total hours: {total_hours} "
                    )

    def write_excel_for_contributors(
        self, excel_file, header_info, summation_info=None, column_widths=None
    ):
        """
        A writer for the project plan of all contributors, one sheet per employee

        Args:
            excel_file (Path): The filename of the Excel file
            header_info (dict): info for the header
            summation_info (dict, optional): info for the summation. Defaults to None
            column_widths (dict, optional): Fix width of specified columns

        Returns:

        """
        _logger.debug(f"Writing to {excel_file} for contributors")
        try:
            projects_per_employee = self.program.tasks
        except AttributeError as err:
            raise AttributeError(
                f"{err}\nproject heeft helemaal geen tasks. Hier gaat what fout"
            )

        if summation_info is not None:
            # Summation info is given. This is done for the key 'total_hours' and 'total_hours_global'
            # Each entry has cell definitions which can contain variables which we are replacing with internal variables
            for summation_var_key, summation_var_info in summation_info.items():

                summation_var_info["hours"] = {
                    "value": summation_var_key,
                    "column_key": "hours",
                    "column_format": "number_format_bold",
                }
        else:
            summation_info = {}

        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            for resource in self.program.get_resources():
                _logger.debug(f"Processing resource {resource}")
                row_index = 0
                total_hours_global = None
                for projects_employee in projects_per_employee:
                    if row_index == 0:
                        header = True
                    else:
                        header = False
                    row_index, level, total_hours_project = write_project_to_excel(
                        project=projects_employee,
                        writer=writer,
                        sheet_name=resource.fullname,
                        header_info=header_info,
                        column_widths=column_widths,
                        resource=resource,
                        row_index=row_index,
                        header=header,
                    )
                    if (
                        "total_hours_project" in summation_info.keys()
                        and total_hours_project is not None
                    ):
                        summation_project_info = deep_copy_dict(
                            summation_info["total_hours_project"]
                        )
                        row_index += 1
                        added_value = False
                        for (
                            sum_project_key,
                            sum_project_properties,
                        ) in summation_project_info.items():
                            value = sum_project_properties["value"]
                            variables = sum_project_properties.get("variables")
                            if variables is not None:
                                for var_key, var_val in variables.items():
                                    try:
                                        variables[var_key] = eval(var_val)
                                    except NameError as name_err:
                                        _logger.warning(name_err)
                                    except (
                                        SyntaxError,
                                        TypeError,
                                    ) as syntax_or_type_error:
                                        _logger.debug(syntax_or_type_error)
                            sum_project_properties["value"] = insert_variables(
                                value, variables_info=variables
                            )
                            try:
                                sum_project_properties["value"] = eval(
                                    sum_project_properties["value"]
                                )
                            except (SyntaxError, TypeError) as syntax_or_type_error:
                                _logger.debug(syntax_or_type_error)

                            write_value_to_named_cell(
                                writer=writer,
                                sheet_name=resource.fullname,
                                row_index=row_index,
                                column_key=sum_project_properties.get(
                                    "column_key", "task"
                                ),
                                cell_format=sum_project_properties.get(
                                    "column_format", "left_align_bold"
                                ),
                                header_info=header_info,
                                value=sum_project_properties["value"],
                            )
                            added_value = True

                        if added_value:
                            row_index += 1

                        # Update the total hours for this project
                        if total_hours_global is None:
                            total_hours_global = 0
                        total_hours_global += total_hours_project

                if (
                    "total_hours_global" in summation_info.keys()
                    and total_hours_global is not None
                ):
                    summation_project_info = deep_copy_dict(
                        summation_info["total_hours_global"]
                    )
                    row_index += 1
                    for (
                        sum_project_key,
                        sum_project_properties,
                    ) in summation_project_info.items():
                        value = sum_project_properties["value"]
                        variables = sum_project_properties.get("variables")
                        if variables is not None:
                            for var_key, var_val in variables.items():
                                try:
                                    variables[var_key] = eval(var_val)
                                except NameError as name_err:
                                    _logger.warning(name_err)
                                except SyntaxError as syntax_or_type_error:
                                    _logger.debug(syntax_or_type_error)
                        sum_project_properties["value"] = insert_variables(
                            value, variables_info=variables
                        )
                        try:
                            sum_project_properties["value"] = eval(
                                sum_project_properties["value"]
                            )
                        except (SyntaxError, TypeError) as syntax_or_type_error:
                            _logger.debug(syntax_or_type_error)
                        write_value_to_named_cell(
                            writer=writer,
                            sheet_name=resource.fullname,
                            row_index=row_index,
                            column_key=sum_project_properties.get("column_key", "task"),
                            cell_format=sum_project_properties.get(
                                "column_format", "left_align_bold"
                            ),
                            header_info=header_info,
                            value=sum_project_properties["value"],
                        )

    def get_dependency(self, key: str) -> gantt.Resource:
        """
        Search the object to which the dependency 'key' refers to

        Parameters
        ----------
        key: str
            Key of the dictionary to which the dependency refers to

        Returns
        -------
        gantt.Resource
            Object to which the  key refers to.
        """

        try:
            depends_of = self.tasks_and_milestones[key]
            if key in self.subprojects.keys():
                _logger.warning(
                    f"The dependency {key} occurs in both tasks en milestones"
                )
            _logger.debug(f"Dependent of task or milestone: {key}")
        except KeyError:
            try:
                depends_of = self.subprojects[key]
                _logger.debug(f"Dependent of project: {key}")
            except KeyError:
                msg = f"Dependency {key} does not exist"
                if self.filter_employees is not None:
                    # in case we are filtering on employees, some dependencies may be missing. Just give a warning
                    _logger.warning(msg)
                    depends_of = None
                else:
                    raise AssertionError(msg)

        return depends_of

    def get_employees(
        self, employees: Union[str, list, dict]
    ) -> EmployeesContributingToTask:
        """
        Turn a list of employees strings into a list of employees gantt.Resource objects

        Parameters
        ---------
        employees: str, list, or dict
            List of employees or, in case just one employee is given, a string. Now, also a dict can be defined
            in order to add a number of hours for an employee to work on the task

        Returns
        -------
        EmployeesContributingToTask: object holding all employees
        """

        contributing_employees = EmployeesContributingToTask()
        if employees is not None:
            if isinstance(employees, str):
                _logger.debug(f"Adding employee: {employees}")
                resource = self.employees[employees].resource
                contributing_employees.add_resource(employees, resource=resource)
            else:
                for employee in employees:
                    _logger.debug(f"Adding employee {employee}")
                    resource = self.employees[employee].resource
                    try:
                        hours = employees.get(employee)
                    except AttributeError:
                        hours = None
                    contributing_employees.add_resource(
                        employee, resource=resource, hours=hours
                    )
        return contributing_employees

    def get_dependencies(self, dependencies: Union[str, dict]) -> list:
        """
        Retrieve all dependencies

        Args:
            dependencies (str or dict): In case the dependency is a string, there is only one.
                This will be obtained from the dict. The dependencies may also be stored in a dict.
                In that case, we retrieve them per item

        Returns
        -------
            List of dependencies
        """

        dependency_elements = list()

        if dependencies is not None:
            if isinstance(dependencies, str):
                dependent_of = self.get_dependency(dependencies)
                dependency_elements.append(dependent_of)
            elif isinstance(dependencies, dict):
                for category, afhankelijk_items in dependencies.items():
                    for task_key in afhankelijk_items:
                        dependent_of = self.get_dependency(task_key)
                        dependency_elements.append(dependent_of)
            else:
                for afhankelijk_item in dependencies:
                    dependent_of = self.get_dependency(afhankelijk_item)
                    dependency_elements.append(dependent_of)

            return dependency_elements

    def add_vacations(self, vacations_info):
        """
        Add all the vacations

        Args:
            vacations_info (dict): information of the vacations
        """
        _logger.info("Adding general holidays")
        for v_key, v_prop in vacations_info.items():
            if v_prop.get("end") is not None:
                _logger.debug(
                    f"Vacation {v_key} from {v_prop['start']} to {v_prop.get('end')}"
                )
            else:
                _logger.debug(f"Vacation {v_key} at {v_prop['start']}")
            self.vacations[v_key] = Vacation(
                start=v_prop["start"], end=v_prop.get("end"), dayfirst=self.dayfirst
            )

    def add_employees(self, employees_info: dict):
        """
        Add the employees with their vacations
        """
        _logger.info("Adding employees...")
        for w_key, w_prop in employees_info.items():
            _logger.debug(f"Adding {w_key} ({w_prop.get('name')})")
            full_name = w_prop.get("name")
            employee_vacations_info = w_prop.get("vacations")
            employee_color = w_prop.get("color")

            self.employees[w_key] = Employee(
                label=w_key,
                full_name=full_name,
                color=employee_color,
                vacations=employee_vacations_info,
            )

            # also add the vacations of this employee to the vacation gantt project in order to give an overview later
            employee_vacations = gantt.Project(
                name=full_name,
                color=employee_color,
                font=gantt.get_font_attributes(font_weight="bold", font_size="20"),
            )
            if employee_vacations_info is not None:
                for v_key, v_prop in employee_vacations_info.items():
                    vacation_name = v_prop.get("label", v_key)
                    vacation_start = v_prop.get("start")
                    vacation_end = v_prop.get("end")
                    if vacation_end is None:
                        vacation_duration = 1
                    else:
                        vacation_duration = None
                    vacation_task = ProjectTask(
                        label=vacation_name,
                        color=v_prop.get("color"),
                        start=vacation_start,
                        end=vacation_end,
                        duration=vacation_duration,
                        dayfirst=self.dayfirst,
                    )
                    employee_vacations.add_task(vacation_task.element)
            self.vacations_gantt.add_task(employee_vacations)

    def make_task_or_milestone(
        self,
        project_leader_key: str = None,
        task_properties: dict = None,
        project_color=None,
        variables_info=None,
        parent=None,
    ) -> Union[ProjectTask, ProjectMileStone]:
        """
        Add all the general tasks and milestones

        Args:
            project_leader_key (str): The key of the project leader
            task_properties (dict): Dictionary with tasks or milestones
            project_color (str): Color of the parent project
            variables_info: (dict, optional): Dictionary with variable information to replace strings. Default to None

        Returns
        -------
        Task or milestone

        """
        dependencies = self.get_dependencies(task_properties.get("dependent_of"))
        element_type = task_properties.get("type", "task")
        if element_type == "task":
            contributing_employees = self.get_employees(
                task_properties.get("employees")
            )
            _logger.debug(f"Voeg task {task_properties.get('label')} toe")
            task_or_milestone = ProjectTask(
                label=insert_variables(task_properties.get("label"), variables_info),
                project_leader_key=project_leader_key,
                start=task_properties.get("start"),
                end=task_properties.get("end"),
                duration=task_properties.get("duration"),
                color=task_properties.get("color"),
                project_color=project_color,
                detail=task_properties.get("detail", False),
                employees=contributing_employees,
                dependent_of=dependencies,
                dayfirst=self.dayfirst,
                variables_info=variables_info,
                parent=parent,
            )
        elif element_type == "milestone":
            _logger.debug(f"Adding milestone {task_properties.get('label')} toe")
            if task_properties.get("end"):
                raise ValueError(
                    "You have specified a milestone, but also defined an end date. Milestones only"
                    f"require a start data. Please fix task\n{task_properties}"
                )
            task_or_milestone = ProjectMileStone(
                label=insert_variables(task_properties.get("label"), variables_info),
                project_leader_key=project_leader_key,
                start=task_properties.get("start"),
                color=task_properties.get("color"),
                project_color=project_color,
                dependent_of=dependencies,
                dayfirst=self.dayfirst,
                parent=parent,
            )
        else:
            raise AssertionError("Type should be 'task' or 'milestone'")

        # add all the remain fields which are not required for the gantt charts but needed for the Excel output
        for task_key, task_value in task_properties.items():
            if not hasattr(task_or_milestone.element, task_key):
                if isinstance(task_value, str):
                    try:
                        _task_value = parse_date(
                            task_value, task_value, dayfirst=self.dayfirst
                        )
                    except ParserError:
                        _logger.debug(f"task {task_key} is not an date. No problem")
                    else:
                        _logger.debug(
                            f"Converted string {task_value} into datetime {_task_value}"
                        )
                        task_value = _task_value
                _logger.debug(f"Adding task {task_key} with value {task_value}")
                setattr(task_or_milestone.element, task_key, task_value)

        return task_or_milestone

    def add_tasks_and_milestones(
        self,
        tasks_and_milestones=None,
        tasks_and_milestones_info=None,
        variables_info=None,
    ):
        """
        Make all tasks en milestones
        """

        _logger.debug("Add all general tasks and milestones")
        if tasks_and_milestones_info is not None:
            # The tasks are organised in modules, to peel of the first level
            tasks_en_mp = dict()
            for module_key, module_values in tasks_and_milestones_info.items():
                _logger.debug(f"Reading tasks of module {module_key}")
                for task_key, task_val in module_values.items():
                    _logger.debug(f"Processing task {task_key}")
                    if task_key in tasks_en_mp.keys():
                        msg = f"De task key {task_key} has been used before. Please pick another name"
                        _logger.warning(msg)
                        raise ValueError(msg)
                    if self.filter_employees is not None:
                        contributors = task_val.get("employees")
                        is_contributing = check_if_employee_in_contributing(
                            filter_employees=self.filter_employees,
                            contributing_employees=contributors,
                        )
                        if not is_contributing:
                            _logger.debug(
                                f"None of {contributors} are in {self.filter_employees}. Skipping"
                            )
                            continue
                    tasks_en_mp[task_key] = tasks_and_milestones_info[module_key][
                        task_key
                    ]
        else:
            tasks_en_mp = tasks_and_milestones

        for task_key, task_val in tasks_en_mp.items():
            _logger.debug(f"Processing task {task_key}")
            self.tasks_and_milestones[task_key] = self.make_task_or_milestone(
                task_properties=task_val, variables_info=variables_info
            )

    def make_projects(
        self,
        project_leader_key,
        subprojects_info,
        subprojects_title,
        subprojects_selection,
        subprojects_color=None,
        variables_info=None,
    ):
        """
        Create all the projects given in subprojects_info

        Args:
            project_leader_key (str): The key of the project leader
            subprojects_info (dict): information per subproject
            subprojects_title (dict): Title of the subprojects
            subprojects_selection (list): List of the subprojects to include at the main level
            subprojects_color (str, optional): Color of the projects. Defaults to None
            variables_info (dict, optional): variables which can be used as replacements over the subprojects. Defaults
                to None

        """
        employee_color = color_to_hex(subprojects_color)

        projects_employee = gantt.Project(
            name=subprojects_title,
            color=employee_color,
            font=gantt.get_font_attributes(font_weight="bold", font_size="20"),
        )

        added_projects = list()

        _logger.info(f"Add all projects of {subprojects_title}")
        for project_key, project_values in subprojects_info.items():
            project_name = project_values.get("title", project_key)
            project_name_collapsed = project_values.get("title_collapsed", project_name)
            projects_employee_collapsed = project_values.get("employees_collapsed")
            if projects_employee_collapsed is not None and isinstance(
                projects_employee_collapsed, str
            ):
                projects_employee_collapsed = [projects_employee_collapsed]

            project_name = insert_variables(project_name, variables_info=variables_info)

            _logger.info(f"Making project: {project_name}")

            project_color = color_to_hex(project_values.get("color"))

            _logger.debug("Creating project {}".format(project_name))
            project = gantt.Project(name=project_name, color=project_color)

            main_start_date = None
            main_end_date = None
            main_contributors = None

            # add all the other elements as attributes
            for p_key, p_value in project_values.items():
                if not hasattr(project, p_key):
                    setattr(project, p_key, p_value)

            if project_key in self.subprojects.keys():
                msg = f"project {project_key} already exists. Pick another name"
                _logger.warning(msg)
                raise ValueError(msg)

            self.subprojects[project_key] = project

            if tasks := project_values.get("tasks"):
                if isinstance(tasks, list):
                    tasks_dict = {k: k for k in tasks}
                else:
                    tasks_dict = tasks

                for task_key, task_val in tasks_dict.items():
                    if isinstance(task_val, dict):
                        is_detail = task_val.get("detail", False)
                    else:
                        is_detail = False
                    if not self.details and is_detail:
                        # We hebben details op False staan en dit is een detail, dus sla deze task over.
                        _logger.info(
                            f"Skipping task {task_key} because it is set to be a detail"
                        )
                        continue

                    _logger.debug("Adding task {}".format(task_key))

                    is_detail = False

                    if isinstance(task_val, str):
                        try:
                            # de task een task of een milestone?
                            task_obj = self.tasks_and_milestones[task_val]
                            task = task_obj.element
                            is_detail = task_obj.detail
                        except KeyError:
                            try:
                                # de task een ander project?
                                task = self.subprojects[task_val]
                            except KeyError as err:
                                if not self.filter_employees:
                                    _logger.warning(f"{err}")
                                    raise
                                else:
                                    _logger.debug(f"{err}")
                                    continue
                    else:
                        task_obj = self.make_task_or_milestone(
                            project_leader_key=project_leader_key,
                            task_properties=task_val,
                            project_color=project_color,
                            variables_info=variables_info,
                            parent=project_key,
                        )
                        task = task_obj.element
                        is_detail = task_obj.detail

                    if task.color is None:
                        task.color = project_color

                    if self.filter_employees:
                        try:
                            contributors = task.employees
                        except AttributeError:
                            if isinstance(task, gantt.Task):
                                _logger.debug(
                                    "No employees found and this is a task. Skip it!"
                                )
                                continue
                            else:
                                _logger.debug(
                                    "No employees found, but can be a projects, so just add"
                                )
                        else:
                            is_contributing = check_if_employee_in_contributing(
                                filter_employees=self.filter_employees,
                                contributing_employees=contributors,
                            )
                            if not is_contributing:
                                _logger.debug(
                                    f"None of {contributors} are in {self.filter_employees}. Skipping"
                                )
                                continue

                    if not self.details and is_detail:
                        _logger.debug(f"skipping task {task_key} as it is a detail")
                    else:
                        if not self.collaps_tasks or isinstance(task, gantt.Project):
                            added_projects.append(project_key)
                            project.add_task(task)

                        if projects_employee_collapsed is None:
                            main_contributors = get_contributors_task(
                                task,
                                main_contributors,
                            )
                        else:
                            main_contributors = get_contributors_from_resources(
                                projects_employee_collapsed,
                                main_contributors,
                                self.employees,
                            )

                        # each project with task is stored as a main project with the project begin and end
                        if (
                            main_start_date is None
                            and self.start_date <= task.start_date() < self.end_date
                        ):
                            main_start_date = task.start_date()
                        try:
                            task_end_date = task.end_date()
                        except AssertionError:
                            main_end_date = None
                        else:
                            main_end_date = min(self.end_date, task_end_date)
                        if (
                            main_start_date is not None
                            and self.start_date < task.start_date() < main_start_date
                        ):
                            main_start_date = task.start_date()

                        if (
                            main_end_date is not None
                            and main_end_date < task.end_date() <= self.end_date
                        ):
                            main_end_date = task.end_date()

            # every project with tasks will be a course project plan as well
            if (
                self.collaps_tasks
                and main_start_date is not None
                and project_key not in added_projects
            ):
                if main_contributors is not None:
                    main_contributors = list(set(main_contributors))
                if main_end_date is None:
                    main_task = gantt.Task(
                        name=project_name_collapsed,
                        start=main_start_date,
                        duration=1,
                        resources=main_contributors,
                    )
                else:
                    main_task = gantt.Task(
                        name=project_name_collapsed,
                        start=main_start_date,
                        stop=main_end_date,
                        resources=main_contributors,
                    )
                if project is not None:
                    project.add_task(main_task)

            self.subprojects[project_key] = project
            if project_key in subprojects_selection:
                # hier project zonder taken toevoegen
                projects_employee.add_task(project)

        # add now all projects of the employee to the program
        self.program.add_task(projects_employee)

    def make_resource_dataframe(self):
        """turn all the resources into a data frame"""

        resources = dict()
        for resource in self.program.get_resources():
            _logger.debug(f"Adding resource {resource.fullname}")
            task_for_resource = dict()
            for task, hours in zip(resource.tasks, resource.task_hours):
                task_for_resource[task.name] = get_task_contribution(
                    resource.name, task, owner_id=self.owner_id
                )
            all_task_for_resource = pd.DataFrame(task_for_resource).T
            all_task_for_resource.index = all_task_for_resource.index.rename(
                self.tasks_id
            )
            all_task_for_resource = all_task_for_resource.reset_index()

            all_task_with_full_owner_name = dict()

            # replace the owner key with the full name of the owner
            for owner_key, owner_df in all_task_for_resource.groupby(self.owner_id):
                try:
                    owner_resource = self.employees[owner_key]
                except KeyError as e:
                    _logger.warning(f"No owner found for {owner_key}: {e}")
                else:
                    all_task_with_full_owner_name[owner_resource.full_name] = owner_df

            df = pd.concat(all_task_with_full_owner_name)
            df = df.drop(self.owner_id, axis=1)
            df = df.reset_index().set_index("level_0")
            df.index = df.index.rename(self.owner_id)
            df = df.drop("level_1", axis=1)
            resources[resource.fullname] = df

        self.tasks_per_resource = pd.concat(resources)
        self.tasks_per_resource.index = self.tasks_per_resource.index.rename(
            [self.employee_id, self.owner_id]
        )
        _logger.debug("Successfully make task per resources")

    def write_planning(
        self,
        planning_output_directory,
        resource_output_directory,
        vacations_output_directory,
        write_resources=False,
        write_vacations=False,
        periods=None,
        suffix=None,
    ):
        """
        Write the planning to the output definitions

        Args:
        planning_output_directory (Path): Output directory of the svg files of the planning
        resource_output_directory (Path): Output directory of the svg files of the resources
        vacations_output_directory (Path): Output directory of the svg files of the vacations
        write_resources (bool, optional): Write the resources file as well. Defaults to False
        write_vacations (bool, optional): Write the vacations file as well. Default to False
        periods (list, optional): Periods we want to add. If None, add all periods. Defaults to None (all periods)
        suffix (str, optional): Add a suffix to the final filename. Defaults to None
        """

        directories = {
            "tasks": planning_output_directory,
            "resources": resource_output_directory,
            "vacations": vacations_output_directory,
        }
        svg42pdf = None
        # make output directories. Vacations can be made per period, so do later
        directories["tasks"].mkdir(parents=True, exist_ok=True)
        if write_resources:
            directories["resources"].mkdir(parents=True, exist_ok=True)

        for period_key, period_prop in self.period_info.items():
            if periods is not None and period_key not in periods:
                _logger.debug(f"Employee {period_key} is skipped")
                continue

            file_names = dict()
            leading_suffix = [period_key]
            if self.collaps_tasks:
                leading_suffix += ["collapsed"]

            write_vacations_this_period = period_prop.get("export_vacations", False)

            for file_suffix in directories.keys():
                file_names[file_suffix] = extend_suffix(
                    self.output_file_name, extensions=leading_suffix + [file_suffix]
                )
                file_names[file_suffix] = (
                    directories[file_suffix] / file_names[file_suffix]
                )

            weeks_margin_left = period_prop.get(
                "weeks_margin_left", self.weeks_margin_left
            )
            weeks_margin_right = period_prop.get(
                "weeks_margin_right", self.weeks_margin_right
            )

            scale = period_prop.get("scale")
            if scale is not None:
                scale = SCALES[scale]
            else:
                scale = self.scale

            start = parse_date(
                period_prop.get("planning_start"),
                self.planning_start,
                dayfirst=self.dayfirst,
            )
            end = parse_date(
                period_prop.get("planning_end"),
                self.planning_end,
                dayfirst=self.dayfirst,
            )

            today = parse_date(
                period_prop.get("today"), self.date_today, dayfirst=self.dayfirst
            )
            if today is not None and scale != SCALES["daily"]:
                # For any scale other than  daily, the today-line is drawn only at Saturdays
                _logger.debug("Change the date to the nearest Saturday")
                _today = today
                today = get_nearest_saturday(today)
                if today != _today:
                    _logger.debug(
                        f"Changing the date today {_today} into the the nearest Saturday {today}"
                    )

            # the planning is a collection of all the projects
            file_name = file_names["tasks"]
            if suffix is not None:
                file_name = extend_suffix(file_name, extensions=suffix)
            _logger.info(
                f"Writing project starting at {start} and ending at {end} with a scale {scale} to {file_name}"
            )
            self.program.make_svg_for_tasks(
                filename=file_name,
                start=start,
                end=end,
                margin_left=weeks_margin_left,
                margin_right=weeks_margin_right,
                scale=scale,
                today=today,
            )

            if self.save_svg_as_pdf:
                try:
                    import svg42pdf
                except ImportError as err:
                    _logger.warning(f"{err}\nFailed writing pdf because svg42pdf is")
                    svg42pdf = None
                else:
                    pdf_file_name = file_name.with_suffix(".pdf")
                    _logger.info(f"Saving as {pdf_file_name}")
                    svg42pdf.svg42pdf(
                        svg_fn=file_name.as_posix(),
                        pdf_fn=pdf_file_name.as_posix(),
                        method="any",
                    )

            if write_resources:
                file_name_resources = file_names["resources"]
                _logger.info(
                    f"Write resources of {start} to {end} with scale {scale} to {file_name_resources}"
                )
                try:
                    self.program.make_svg_for_resources(
                        filename=file_name_resources.as_posix(),
                        start=start,
                        end=end,
                        scale=SCALES["daily"],
                        today=today,
                    )
                except TypeError as err:
                    _logger.warning(err)
                    _logger.warning(
                        "Failed writing the resources with the above error message. Please check your "
                        "employee's input data"
                    )
                else:
                    if self.save_svg_as_pdf and svg42pdf is not None:
                        pdf_file_name_res = file_name_resources.with_suffix(".pdf")
                        svg42pdf.svg42pdf(
                            svg_fn=file_name_resources.as_posix(),
                            pdf_fn=pdf_file_name_res.as_posix(),
                            method="any",
                        )

            if write_vacations or write_vacations_this_period:
                file_name_vacations = file_names["vacations"]
                vacations_output_directory.mkdir(exist_ok=True, parents=True)
                _logger.info(f"Writing vacation file {file_name_vacations}")
                self.vacations_gantt.make_svg_for_tasks(
                    filename=file_name_vacations,
                    start=start,
                    end=end,
                    margin_left=weeks_margin_left,
                    margin_right=weeks_margin_right,
                    scale=scale,
                    today=today,
                )
                if self.save_svg_as_pdf and svg42pdf is not None:
                    pdf_file_name_vac = file_name_vacations.with_suffix(".pdf")
                    svg42pdf.svg42pdf(
                        svg_fn=file_name_vacations.as_posix(),
                        pdf_fn=pdf_file_name_vac.as_posix(),
                        method="any",
                    )

            _logger.debug("Done")


def check_if_employee_in_contributing(
    filter_employees: list, contributing_employees: list
) -> bool:
    """
    Check if any of the employees given in filter_employees is in contributing to this taks
    """

    is_contributing = False

    if contributing_employees:
        if isinstance(contributing_employees, str):
            contributing_employees = set(list([contributing_employees]))
        else:
            contributing_employees = set(contributing_employees)
        if contributing_employees.intersection(filter_employees):
            _logger.debug(
                f"Contributing employees {contributing_employees} not in filter list"
            )
            is_contributing = True

    return is_contributing


def extend_suffix(output_filename: Path, extensions: Union[list, str]):
    """
    Add an extra suffix to the base filename

    Parameters
    ----------
    output_filename: Path
        Base filename
    extensions: str or list
        Extra suffixes to add

    Returns
    -------
    Path:
        New filename with extra suffix

    """
    suffix = output_filename.suffix
    if isinstance(extensions, str):
        extensions = [extensions]
    output_filename = Path(
        "_".join([output_filename.with_suffix("").as_posix()] + extensions)
    ).with_suffix(suffix)

    return output_filename


def get_contributors_task(task, contributors):
    """
    get of the contributors of this Task based on the task resources

    Parameters
    ----------
    task
    contributors

    Returns
    -------
    list:
        contributors

    """
    try:
        task_resources = task.resources
    except AttributeError:
        pass
    else:
        if task_resources:
            for employee in task_resources:
                if contributors is None:
                    contributors = [employee]
                else:
                    contributors.append(employee)
    return contributors


def get_contributors_from_resources(
    projects_employee_global, contributors, all_resources
):
    """
    get the contributors of this Task based on the global resources

    Parameters
    ----------
    projects_employee_global
    contributors
    all_resources: dict

    Returns
    -------
    list:
        contributors

    """
    for emp_key, emp_val in all_resources.items():
        if emp_key in projects_employee_global:
            if contributors is None:
                contributors = [emp_val.resource]
            else:
                contributors.append(emp_val.resource)
    return contributors
