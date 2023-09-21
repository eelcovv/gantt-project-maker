import locale
import logging
from datetime import datetime
from pathlib import Path
from typing import Union

import dateutil.parser as dparse

import gantt_project_maker.gantt as gantt
import gantt_project_maker.colors as cbsc
from gantt_project_maker.colors import color_to_hex
from gantt_project_maker.excelwriter import write_planning_to_excel

locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")

cbsc.set_cbs_colors()

SCALES = dict(
    daily=gantt.DRAW_WITH_DAILY_SCALE,
    weekly=gantt.DRAW_WITH_WEEKLY_SCALE,
    monthly=gantt.DRAW_WITH_MONTHLY_SCALE,
    quarterly=gantt.DRAW_WITH_QUATERLY_SCALE,
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


def voeg_vacations_employee_toe(
    Employee: gantt.Resource, vakantie_lijst: dict
) -> dict:
    """
    Voeg de vakantiedagen van een werknemer toe

    Parameters
    ----------
    Employee: gannt.Resource
        De Employee waarvan je de vakantie dagen gaat toevoegen
    vakantie_lijst: dict
        Een dictionary met items per vakantie. Per vakantie heb je een start en een end

    Returns
    -------
    dict:
        Dictionary met de vacations.
    """
    vacations = dict()

    if vakantie_lijst is not None:
        for vakantie_key, vakantie_prop in vakantie_lijst.items():
            vacations[vakantie_key] = Vakantie(
                vakantie_prop["start"], vakantie_prop.get("end"), werknemer=Employee
            )
    return vacations


def define_attributes():
    gantt.define_font_attributes(
        fill="black", stroke="black", stroke_width=0, font_family="Verdana"
    )


class StartEindBase:
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


class Vakantie(StartEindBase):
    def __init__(self, start, end=None, werknemer=None):
        super().__init__(start, end)

        if werknemer is None:
            self.pool = gantt
        else:
            self.pool = werknemer

        self.add_vacation()

    def add_vacation(self):
        """
        Voeg de gemeenschappelijke vakantiedagen toe
        """
        self.pool.add_vacations(self.start, self.end)


class Employee:
    def __init__(self, label, volledige_naam=None, vakantie_lijst=None):
        self.label = label
        self.volledige_naam = volledige_naam
        self.resource = gantt.Resource(name=label, fullname=volledige_naam)

        if vakantie_lijst is not None:
            self.vacations = voeg_vacations_employee_toe(
                Employee=self.resource, vakantie_lijst=vakantie_lijst
            )
        else:
            self.vacations = None


class BasicElement(StartEindBase):
    def __init__(
        self,
        label,
        start=None,
        afhankelijk_van=None,
        color=None,
        volledige_naam=None,
        detail=False,
        display=True,
        remark=None,
    ):
        super().__init__(start, start)
        if label is None:
            raise ValueError("Iedere task moet een label hebben!")
        self.label = label
        self.detail = detail
        self.afhankelijk_van = afhankelijk_van
        self.color = color_to_hex(color)
        self.volledige_naam = volledige_naam
        self.display = display

        self.remark = remark


class task(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        end=None,
        duur=None,
        employees=None,
        afhankelijk_van=None,
        color=None,
        volledige_naam=None,
        percentage_voltooid=None,
        detail=False,
        display=True,
        deadline=None,
        focal_point=None,
        dvz=None,
        cci=None,
        remark=None,
    ):
        super().__init__(
            label=label,
            start=start,
            afhankelijk_van=afhankelijk_van,
            color=color,
            detail=detail,
            volledige_naam=volledige_naam,
            display=display,
            remark=remark,
        )
        self.end = parse_date(end)
        self.duur = duur
        self.employees = employees
        self.percentage_voltooid = percentage_voltooid

        self.element = None

        # extra velden die je toe kan voegen
        self.deadline = parse_date(deadline, deadline)
        self.focal_point = focal_point
        self.dvz = dvz
        self.cci = cci

        self.voeg_task_toe()

    def voeg_task_toe(self):
        self.element = gantt.Task(
            name=self.label,
            start=self.start,
            stop=self.end,
            duration=self.duur,
            depends_of=self.afhankelijk_van,
            resources=self.employees,
            color=self.color,
            percent_done=self.percentage_voltooid,
        )

        self.element.deadline = self.deadline
        self.element.focal_point = self.focal_point
        self.element.dvz = self.dvz
        self.element.cci = self.cci
        self.element.remark = self.remark


class Mijlpaal(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        afhankelijk_van=None,
        color=None,
        detail=False,
        volledige_naam=None,
        display=True,
        remark=None,
    ):
        super().__init__(
            label=label,
            start=start,
            afhankelijk_van=afhankelijk_van,
            color=color,
            detail=detail,
            volledige_naam=volledige_naam,
            display=display,
            remark=remark,
        )

        self.element = None

        self.voeg_mijlpaal_toe()

    def voeg_mijlpaal_toe(self):
        self.element = gantt.Milestone(
            name=self.label,
            start=self.start,
            depends_of=self.afhankelijk_van,
            color=self.color,
        )
        self.element.remark = self.remark


class ProjectPlanner:
    def __init__(
        self,
        programma_title=None,
        programma_color=None,
        output_file_name=None,
        planning_start=None,
        planning_end=None,
        vandaag=None,
        scale=None,
        period_info=None,
        excel_info=None,
        details=None,
    ):
        self.period_info = period_info
        self.planning_start = planning_start
        self.planning_end = planning_end
        self.datum_vandaag = vandaag
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
        self.subprojecten = dict()

    @staticmethod
    def add_global_information():
        define_attributes()

    def maak_planning(self):
        """
        Deze hoofdmethode maakt alle elementen aan
        """

    def exporteer_naar_excel(self, excel_output_directory):
        """
        Schrijf de planning naar een excel file

        Parameters
        ----------
        excel_output_directory: Path
            Output directory van excel files
        """

        if self.excel_info is None:
            _logger.warning("Voeg Excel info toe aan je settings file")
        else:
            excel_output_directory.mkdir(exist_ok=True)
            excel_file = excel_output_directory / self.output_file_name.with_suffix(
                ".xlsx"
            )
            _logger.info(f"Exporteer de planning naar {excel_file}")
            write_planning_to_excel(
                excel_file=excel_file,
                project=self.programma,
                header_info=self.excel_info["header"],
                column_widths=self.excel_info.get("column_widths"),
            )

    def get_afhankelijkheid(self, key: str) -> gantt.Resource:
        """
        Zoek het object waar de afhankelijkheid 'key' naar verwijst
        Parameters
        ----------
        key: str
            Key van de dictionary waar de afhankelijkheid naar verwijst

        Returns
        -------
        gantt.Resource
            Afhankelijkheid waar key naar verwijst.
        """

        try:
            hangt_af_van = self.tasks_and_milestones[key]
            if key in self.subprojecten.keys():
                _logger.warning(
                    f"De afhankelijkheid {key} komt in zowel tasks en mijlpalen als in subprojecten voor"
                )
            _logger.debug(f"Afhankelijk van task of mijlpaal: {key}")
        except KeyError:
            try:
                hangt_af_van = self.subprojecten[key]
                _logger.debug(f"Afhankelijk van project: {key}")
            except KeyError:
                raise AssertionError(f"Afhankelijkheid {key} bestaat niet")

        return hangt_af_van

    def get_employees(self, employees: Union[str, list]) -> list:
        """
        Zet een lijst van employees strings om in een lijst van employees gannt.Resource objecten

        Parameters
        ----------
        employees: list of str
            Lijst van employees of, in het geval er maar 1 Employee is, een string

        Returns
        -------
        list:
            Lijst van employees resource objecten.

        """

        employees_elementen = list()
        if employees is not None:
            if isinstance(employees, str):
                _logger.debug(f"Voeg Employee toe: {employees}")
                employees_elementen.append(self.employees[employees].resource)
            else:
                for Employee in employees:
                    _logger.debug(f"Voeg toe Employee {Employee}")
                    employees_elementen.append(self.employees[Employee].resource)
        return employees_elementen

    def get_afhankelijkheden(self, afhankelijkheden: Union[str, dict]) -> list:
        """
        Haal alle afhankelijke objecten op

        Parameters
        ----------
        afhankelijkheden: str or dict
            Als afhankelijkheid een string is hebben we er maar een. Deze wordt uit de dict gehaald
            De afhankelijkheden kunnen ook in een dict opgeslagen zijn. Dan halen we ze per item op
        Returns
        -------
        list:
            Lijst met de afhankelijkheden.

        """

        afhankelijks_elementen = list()

        if afhankelijkheden is not None:
            if isinstance(afhankelijkheden, str):
                afhankelijk_van = self.get_afhankelijkheid(afhankelijkheden)
                afhankelijks_elementen.append(afhankelijk_van)
            elif isinstance(afhankelijkheden, dict):
                for category, afhankelijk_items in afhankelijkheden.items():
                    for task_key in afhankelijk_items:
                        afhankelijk_van = self.get_afhankelijkheid(task_key)
                        afhankelijks_elementen.append(afhankelijk_van)
            else:
                for afhankelijk_item in afhankelijkheden:
                    afhankelijk_van = self.get_afhankelijkheid(afhankelijk_item)
                    afhankelijks_elementen.append(afhankelijk_van)

            return afhankelijks_elementen

    def add_vacations(self, vacations_info):
        """
        Voeg alle algemene vacations toe
        """
        # Change font default

        # voeg de algemene vacations toe
        _logger.info("Voeg algemene vakantiedagen toe")
        for v_key, v_prop in vacations_info.items():
            if v_prop.get("end") is not None:
                _logger.debug(
                    f"Vakantie {v_key} van {v_prop['start']} to {v_prop.get('end')}"
                )
            else:
                _logger.debug(f"Vakantie {v_key} op {v_prop['start']}")
            self.vacations[v_key] = Vakantie(
                start=v_prop["start"], end=v_prop.get("end")
            )

    def add_employees(self, employees_info):
        """
        Voeg de employees met hun vacations toe.
        """
        _logger.info("Voeg employees toe")
        for w_key, w_prop in employees_info.items():
            _logger.debug(f"Voeg {w_key} ({w_prop.get('naam')}) toe")
            self.employees[w_key] = Employee(
                label=w_key,
                volledige_naam=w_prop.get("naam"),
                vakantie_lijst=w_prop.get("vacations"),
            )

    def maak_task_of_mijlpaal(
        self, task_eigenschappen: dict = None
    ) -> Union[task, Mijlpaal]:
        """
        Voeg alle algemene tasks en mijlpalen toe

        Parameters
        ----------
        task_eigenschappen:

        Returns
        -------

        """
        afhankelijkheden = self.get_afhankelijkheden(
            task_eigenschappen.get("afhankelijk_van")
        )
        element_type = task_eigenschappen.get("type", "task")
        if element_type == "task":
            employees = self.get_employees(task_eigenschappen.get("employees"))
            _logger.debug(f"Voeg task {task_eigenschappen.get('label')} toe")
            task_of_mijlpaal = task(
                label=task_eigenschappen.get("label"),
                start=task_eigenschappen.get("start"),
                end=task_eigenschappen.get("end"),
                duur=task_eigenschappen.get("duur"),
                color=task_eigenschappen.get("color"),
                detail=task_eigenschappen.get("detail", False),
                employees=employees,
                afhankelijk_van=afhankelijkheden,
                deadline=task_eigenschappen.get("deadline"),
                focal_point=task_eigenschappen.get("focal_point"),
                dvz=task_eigenschappen.get("dvz"),
                cci=task_eigenschappen.get("cci"),
                remark=task_eigenschappen.get("remark"),
            )
        elif element_type == "mijlpaal":
            _logger.debug(f"Voeg mijlpaal {task_eigenschappen.get('label')} toe")
            task_of_mijlpaal = Mijlpaal(
                label=task_eigenschappen.get("label"),
                start=task_eigenschappen.get("start"),
                color=task_eigenschappen.get("color"),
                afhankelijk_van=afhankelijkheden,
                remark=task_eigenschappen.get("remark"),
            )
        else:
            raise AssertionError("Type should be 'task' or 'mijlpaal'")

        return task_of_mijlpaal

    def add_tasks_and_milestones(
        self, tasks_and_milestones=None, tasks_and_milestones_info=None
    ):
        """
        Maak alle tasks en mijlpalen
        """

        _logger.info("Voeg alle algemene tasks en mijlpalen toe")
        if tasks_and_milestones_info is not None:
            # We voegen hier een dictionary van tasks en mijlpalen toe
            # Die zijn in modules georganiseerd, haal hier het eerste niveau eraf.
            tasks_en_mp = dict()
            for module_key, module_values in tasks_and_milestones_info.items():
                _logger.debug(f"lezen tasks van module {module_key}")
                for task_key, task_val in module_values.items():
                    _logger.debug(f"Processen task {task_key}")
                    if task_key in tasks_en_mp.keys():
                        msg = f"De task key {task_key} is al eerder gebruikt. Kies een andere naam!"
                        _logger.warning(msg)
                        raise ValueError(msg)
                    tasks_en_mp[task_key] = tasks_and_milestones_info[module_key][
                        task_key
                    ]
        else:
            tasks_en_mp = tasks_and_milestones

        for task_key, task_val in tasks_en_mp.items():
            _logger.debug(f"Processen task {task_key}")
            self.tasks_and_milestones[task_key] = self.maak_task_of_mijlpaal(
                task_eigenschappen=task_val
            )

    def make_projects(
        self,
        subprojects_info,
        subprojects_title,
        subprojects_selection,
        subprojects_color=None,
    ):
        """
        Maak alle projecten
        """
        employee_color = color_to_hex(subprojects_color)
        projects_employee = gantt.Project(
            name=subprojects_title, color=employee_color
        )

        _logger.info(f"Voeg alle projecten toe van {subprojects_title}")
        for project_key, project_values in subprojects_info.items():
            _logger.info(f"Maak project: {project_values['title']}")

            project_name = project_values["title"]

            project_color = color_to_hex(project_values.get("color"))

            _logger.debug("Creating project {}".format(project_name))
            project = gantt.Project(name=project_name, color=project_color)

            # add all the other elements as attributes
            for p_key, p_value in project_values.items():
                if not hasattr(project, p_key):
                    setattr(project, p_key, p_value)

            if project_key in self.subprojecten.keys():
                msg = f"project {project_key} bestaat al. Kies een andere naam"
                _logger.warning(msg)
                raise ValueError(msg)

            self.subprojecten[project_key] = project

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
                            f"Sla task {task_key} over omdat het een detail is"
                        )
                        continue

                    _logger.debug("Adding task {}".format(task_key))

                    is_detail = False

                    if isinstance(task_val, str):
                        try:
                            # de task een task of een mijlpaal?
                            task_obj = self.tasks_and_milestones[task_val]
                            task = task_obj.element
                            is_detail = task_obj.detail
                        except KeyError:
                            try:
                                # de task een ander project?
                                task = self.subprojecten[task_val]
                            except KeyError as err:
                                _logger.warning(f"{err}")
                                raise
                    else:
                        task_obj = self.maak_task_of_mijlpaal(
                            task_eigenschappen=task_val
                        )
                        task = task_obj.element
                        is_detail = task_obj.detail

                    if not self.details and is_detail:
                        _logger.debug(f"skipping task {task_key} as it is a detail")
                    else:
                        project.add_task(task)

            self.subprojecten[project_key] = project
            if project_key in subprojects_selection:
                projects_employee.add_task(project)

        # voeg nu alle projecten van de Employee aan het programma toe
        self.programma.add_task(projects_employee)

    def write_planning(
        self,
        planning_output_directory,
        resource_output_directory,
        schrijf_resources=False,
        periods=None,
    ):
        """
        Schrijf de planning naar de output definities.

        Parameters
        ----------
        schrijf_resources: bool
            Schrijf de resources file
        planning_output_directory: Path
            Output directory van de svg files van de planning
        resource_output_directory: Path
            Output directory van de svg files van de resources
        periods: list
            Lijst van periods die we toevoegen. Als None voegen we alles toe
        """

        for period_key, period_prop in self.period_info.items():

            if periods is not None and period_key not in periods:
                _logger.debug(f"Employee {period_key} wordt over geslagen")
                continue

            suffix = self.output_file_name.suffix
            file_base_tasks = "_".join(
                [self.output_file_name.with_suffix("").as_posix(), period_key, "tasks"]
            )
            file_base_resources = file_base_tasks.replace("_tasks", "_resources")

            planning_output_directory.mkdir(exist_ok=True, parents=True)

            if schrijf_resources:
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
                # voor een scale anders dan dagelijks wordt de vandaaglijn alleen op zaterdag getekend!
                _logger.debug("Verander datum op dichtstbijzijnde zaterdag")
                _today = today
                today = get_nearest_saturday(today)
                if today != _today:
                    _logger.debug(
                        f"Verander vandaag datum {_today} in dichtstbijzijnde zaterdag {today}"
                    )

            # the planning is a collection of all the projects
            _logger.info(
                f"Schrijf project van {start} tot {end} met scale {scale} naar {file_name}"
            )
            self.programma.make_svg_for_tasks(
                filename=file_name.as_posix(),
                start=start,
                end=end,
                scale=scale,
                today=today,
            )
            _logger.debug("Done")

            if schrijf_resources:
                _logger.info(
                    f"Schrijf resources van {start} tot {end} met scale {scale} naar {file_name_res}"
                )
                self.programma.make_svg_for_resources(
                    filename=file_name_res.as_posix(),
                    start=start,
                    end=end,
                    scale=scale,
                    today=today,
                )
            _logger.debug("Done")
