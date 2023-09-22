import logging
from datetime import datetime
from pathlib import Path
from typing import Union

from dateutil.parser import ParserError
import dateutil.parser as dparse

import gantt_project_maker.gantt as gantt
from gantt_project_maker.colors import color_to_hex
from gantt_project_maker.excelwriter import write_planning_to_excel


SCALES = dict(
    daily=gantt.DRAW_WITH_DAILY_SCALE,
    weekly=gantt.DRAW_WITH_WEEKLY_SCALE,
    monthly=gantt.DRAW_WITH_MONTHLY_SCALE,
    quarterly=gantt.DRAW_WITH_QUARTERLY_SCALE,
)

_logger = logging.getLogger(__name__)


def get_nearest_saturday(date):
    """
    Verkrijg de eerste zaterdag op basis van de

    Parameters
    ----------
    date

    Returns
    -------

    """
    d = date.toordinal()
    last = d - 6
    sunday = last - (last % 7)
    saturday = sunday + 6
    if d - saturday > 7 / 2:
        # de afstand tot vorige zaterdag is meer dan een halve week, dus de volgende zaterdag is dichter bij
        saturday += 7
    return date.fromordinal(saturday)


def parse_date(date_string: str, date_default: str = None) -> datetime.date:
    """
    Lees de date_string en parse de datum

    Parameters
    ----------
    date_string: str
        Datum representatie
    date_default:
        Als de date_string None is deze default waarde genomen.

    Returns
    -------
    datetime.date():
        Datum
    """
    if date_string is not None:
        date = dparse.parse(date_string, dayfirst=True).date()
    elif date_default is not None and isinstance(date_default, str):
        date = dparse.parse(date_default, dayfirst=True).date()
    else:
        date = date_default
    return date


def add_vacation_employee(employee: gantt.Resource, vacations: dict) -> dict:
    """
    Add the vacations of an employee

    Parameters
    ----------
    employee: gannt.Resource
        The employee for who you want to add the vacation
    vacations: dict
        A dictionary with items per vacation. Per vakantion you need a start and an end

    Returns
    -------
    dict:
        Dictionary with the vacations.
    """
    vacations = dict()

    if vacations is not None:
        for vacation_key, vacation_properties in vacations.items():
            vacations[vacation_key] = Vacation(
                vacation_properties["start"],
                vacation_properties.get("end"),
                werknemer=employee,
            )
    return vacations


def define_attributes():

    gantt.define_font_attributes(
        fill="black", stroke="black", stroke_width=0, font_family="Verdana"
    )


class StartEndBase:
    """
    Basis van alle classes met een begin- en einddatum.
    """

    def __init__(self, start: str, end: str = None):
        """
        Sla de datum stings op als datetime objecten

        Parameters
        ----------
        start: str
            Startdatum is verplicht
        end: str or None
            Einddatum is optioneel.
        """
        self.start = parse_date(start)
        self.end = parse_date(end)


class Vacation(StartEndBase):
    def __init__(self, start, end=None, werknemer=None):
        super().__init__(start, end)

        if werknemer is None:
            self.pool = gantt
        else:
            self.pool = werknemer

        self.add_vacation()

    def add_vacation(self):
        """
        Add common vacations
        """
        self.pool.add_vacations(self.start, self.end)


class Employee:
    def __init__(self, label, full_name=None, vacations=None):
        self.label = label
        self.full_name = full_name
        self.resource = gantt.Resource(name=label, fullname=full_name)

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
        start=None,
        dependent_of=None,
        color=None,
        detail=False,
        display=True,
    ):
        super().__init__(start, start)
        if label is None:
            raise ValueError("Every task should have a label!")
        self.label = label
        self.detail = detail
        self.dependent_of = dependent_of
        self.color = color_to_hex(color)
        self.display = display


class Task(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        end=None,
        duration=None,
        employees=None,
        dependent_of=None,
        color=None,
        detail=False,
        display=True,
    ):
        super().__init__(
            label=label,
            start=start,
            dependent_of=dependent_of,
            color=color,
            detail=detail,
            display=display,
        )
        self.end = parse_date(end)
        self.duration = duration
        self.employees = employees

        self.element = self.add_task()

    def add_task(self) -> gantt.Task:
        task = gantt.Task(
            name=self.label,
            start=self.start,
            stop=self.end,
            duration=self.duration,
            depends_of=self.dependent_of,
            resources=self.employees,
            color=self.color,
        )
        return task


class Milestone(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        dependent_of=None,
        color=None,
        detail=False,
        display=True,
    ):
        super().__init__(
            label=label,
            start=start,
            dependent_of=dependent_of,
            color=color,
            detail=detail,
            display=display,
        )

        self.element = self.add_milestone()

    def add_milestone(self) -> gantt.Milestone:
        element = gantt.Milestone(
            name=self.label,
            start=self.start,
            depends_of=self.dependent_of,
            color=self.color,
        )
        return element


class ProjectPlanner:
    def __init__(
        self,
        programma_title=None,
        programma_color=None,
        output_file_name=None,
        planning_start=None,
        planning_end=None,
        today=None,
        scale=None,
        period_info=None,
        excel_info=None,
        details=None,
    ):
        self.period_info = period_info
        self.planning_start = planning_start
        self.planning_end = planning_end
        self.datum_vandaag = today
        self.scale = scale
        self.details = details

        self.excel_info = excel_info

        if output_file_name is None:
            self.output_file_name = Path("gantt_projects.svg")
        else:
            self.output_file_name = Path(output_file_name)

        # het hoofdproject maken we alvast aan.
        self.programma = gantt.Project(
            name=programma_title, color=color_to_hex(programma_color)
        )

        self.project_tasks = dict()
        self.vacations = dict()
        self.employees = dict()
        self.tasks_and_milestones = dict()
        self.subprojects = dict()

    @staticmethod
    def add_global_information():
        define_attributes()

    def exporteer_naar_excel(self, excel_output_directory):
        """
        Write planning to an Excel file

        Parameters
        ----------
        excel_output_directory: Path
            Output directory of the Excel files
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
            _logger.info(f"Exporting planning to {excel_file}")
            write_planning_to_excel(
                excel_file=excel_file,
                project=self.programma,
                header_info=self.excel_info["header"],
                column_widths=self.excel_info.get("column_widths"),
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
                raise AssertionError(f"Dependency {key} does not exist")

        return depends_of

    def get_employees(self, employees: Union[str, list]) -> list:
        """
        Turn a list of employees strings into a list of employees gannt.Resource objects

        Parameters
        ----------
        employees: list of str
            List of employees or, in case just one employee is given, a string


        Returns
        -------
        list:
            List of employees resource objects
        """

        employees_elements = list()
        if employees is not None:
            if isinstance(employees, str):
                _logger.debug(f"Adding employee: {employees}")
                employees_elements.append(self.employees[employees].resource)
            else:
                for employee in employees:
                    _logger.debug(f"Adding employee {employee}")
                    employees_elements.append(self.employees[employee].resource)
        return employees_elements

    def get_dependencies(self, dependencies: Union[str, dict]) -> list:
        """
        Retrieve all dependencies

        Parameters
        ----------
        dependencies: str or dict
            In case the dependency is a string, there is only one. This will be obtained from the dict.
            The dependencies may also be stored in a dict. In that case, we retrieve them per item

        Returns
        -------
        list:
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
                start=v_prop["start"], end=v_prop.get("end")
            )

    def add_employees(self, employees_info):
        """
        Add the employees with their vacations
        """
        _logger.info("Adding employees...")
        for w_key, w_prop in employees_info.items():
            _logger.debug(f"Adding {w_key} ({w_prop.get('name')})")
            self.employees[w_key] = Employee(
                label=w_key,
                full_name=w_prop.get("name"),
                vacations=w_prop.get("vacations"),
            )

    def make_task_of_milestone(
        self, task_properties: dict = None
    ) -> Union[Task, Milestone]:
        """
        Add all the general tasks and milestones

        Parameters
        ----------
        task_properties: dict
            Dictionary with tasks or milestones

        Returns
        -------
        Task or milestone

        """
        dependencies = self.get_dependencies(task_properties.get("dependent_of"))
        element_type = task_properties.get("type", "task")
        if element_type == "task":
            employees = self.get_employees(task_properties.get("employees"))
            _logger.debug(f"Voeg task {task_properties.get('label')} toe")
            task_or_milestone = Task(
                label=task_properties.get("label"),
                start=task_properties.get("start"),
                end=task_properties.get("end"),
                duration=task_properties.get("duration"),
                color=task_properties.get("color"),
                detail=task_properties.get("detail", False),
                employees=employees,
                dependent_of=dependencies,
            )
        elif element_type == "milestone":
            _logger.debug(f"Adding milestone {task_properties.get('label')} toe")
            task_or_milestone = Milestone(
                label=task_properties.get("label"),
                start=task_properties.get("start"),
                color=task_properties.get("color"),
                dependent_of=dependencies,
            )
        else:
            raise AssertionError("Type should be 'task' or 'milestone'")

        # add all the remain fields which are not required for the gantt charts but needed for the Excel output
        for task_key, task_value in task_properties.items():
            if not hasattr(task_or_milestone.element, task_key):
                if isinstance(task_value, str):
                    try:
                        _task_value = parse_date(task_value, task_value)
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
        self, tasks_and_milestones=None, tasks_and_milestones_info=None
    ):
        """
        Make all tasks en milestones
        """

        _logger.info("Voeg alle algemene tasks en mijlpalen toe")
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
                    tasks_en_mp[task_key] = tasks_and_milestones_info[module_key][
                        task_key
                    ]
        else:
            tasks_en_mp = tasks_and_milestones

        for task_key, task_val in tasks_en_mp.items():
            _logger.debug(f"Processing task {task_key}")
            self.tasks_and_milestones[task_key] = self.make_task_of_milestone(
                task_properties=task_val
            )

    def make_projects(
        self,
        subprojects_info,
        subprojects_title,
        subprojects_selection,
        subprojects_color=None,
    ):
        """
        Make all projects
        """
        employee_color = color_to_hex(subprojects_color)
        projects_employee = gantt.Project(name=subprojects_title, color=employee_color)

        _logger.info(f"Add all projects of {subprojects_title}")
        for project_key, project_values in subprojects_info.items():
            _logger.info(f"Making project: {project_values['title']}")

            project_name = project_values["title"]

            project_color = color_to_hex(project_values.get("color"))

            _logger.debug("Creating project {}".format(project_name))
            project = gantt.Project(name=project_name, color=project_color)

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
                                _logger.warning(f"{err}")
                                raise
                    else:
                        task_obj = self.make_task_of_milestone(task_properties=task_val)
                        task = task_obj.element
                        is_detail = task_obj.detail

                    if not self.details and is_detail:
                        _logger.debug(f"skipping task {task_key} as it is a detail")
                    else:
                        project.add_task(task)

            self.subprojects[project_key] = project
            if project_key in subprojects_selection:
                projects_employee.add_task(project)

        # add now all projects of the employee to the program
        self.programma.add_task(projects_employee)

    def write_planning(
        self,
        planning_output_directory,
        resource_output_directory,
        write_resources=False,
        periods=None,
    ):
        """
        Write the planning to the output definitions

        Parameters
        ----------
        write_resources: bool
            Write the resources file as well (next to the gantt charts which is always written)
        planning_output_directory: Path
            Output directory van de svg files van de planning
        resource_output_directory: Path
            Output directory van de svg files van de resources
        periods: list
            List of periods we want to add. If None, add all periods
        """

        for period_key, period_prop in self.period_info.items():

            if periods is not None and period_key not in periods:
                _logger.debug(f"Employee {period_key} is skipped")
                continue

            suffix = self.output_file_name.suffix
            file_base_tasks = "_".join(
                [self.output_file_name.with_suffix("").as_posix(), period_key, "tasks"]
            )
            file_base_resources = file_base_tasks.replace("_tasks", "_resources")

            planning_output_directory.mkdir(exist_ok=True, parents=True)

            if write_resources:
                resource_output_directory.mkdir(exist_ok=True, parents=True)

            file_name = planning_output_directory / Path(file_base_tasks).with_suffix(
                suffix
            )
            file_name_res = resource_output_directory / Path(
                file_base_resources
            ).with_suffix(suffix)

            scale = period_prop.get("scale")
            if scale is not None:
                scale = SCALES[scale]
            else:
                scale = self.scale

            start = parse_date(period_prop.get("planning_start"), self.planning_start)
            end = parse_date(period_prop.get("planning_end"), self.planning_end)
            today = parse_date(period_prop.get("vandaag"), self.datum_vandaag)
            if scale != SCALES["daily"]:
                # For any scale other than  daily, the today-line is drawn only at Saturdays
                _logger.debug("Change the date to the nearest Saturday")
                _today = today
                today = get_nearest_saturday(today)
                if today != _today:
                    _logger.debug(
                        f"Changing the date today {_today} into the the nearest Saturday {today}"
                    )

            # the planning is a collection of all the projects
            _logger.info(
                f"Writing project starting at {start} and ending at {end} with a scale {scale} to {file_name}"
            )
            self.programma.make_svg_for_tasks(
                filename=file_name.as_posix(),
                start=start,
                end=end,
                scale=scale,
                today=today,
            )
            _logger.debug("Done")

            if write_resources:
                _logger.info(
                    f"Write resources of {start} to {end} with scale {scale} to {file_name_res}"
                )
                self.programma.make_svg_for_resources(
                    filename=file_name_res.as_posix(),
                    start=start,
                    end=end,
                    scale=scale,
                    today=today,
                )
            _logger.debug("Done")
