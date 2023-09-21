import locale
import logging
from datetime import datetime
from pathlib import Path
from typing import Union

import dateutil.parser as dparse

import gantt
import gantt_projectplanner.colors as cbsc
from gantt_projectplanner.colors import color_to_hex
from gantt_projectplanner.excelwriter import write_planning_to_excel

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


def voeg_vakanties_medewerker_toe(
    medewerker: gantt.Resource, vakantie_lijst: dict
) -> dict:
    """
    Voeg de vakantiedagen van een werknemer toe

    Parameters
    ----------
    medewerker: gannt.Resource
        De medewerker waarvan je de vakantie dagen gaat toevoegen
    vakantie_lijst: dict
        Een dictionary met items per vakantie. Per vakantie heb je een start en een einde

    Returns
    -------
    dict:
        Dictionary met de vakanties.
    """
    vakanties = dict()

    if vakantie_lijst is not None:
        for vakantie_key, vakantie_prop in vakantie_lijst.items():
            vakanties[vakantie_key] = Vakantie(
                vakantie_prop["start"], vakantie_prop.get("einde"), werknemer=medewerker
            )
    return vakanties


def define_attributes():
    gantt.define_font_attributes(
        fill="black", stroke="black", stroke_width=0, font_family="Verdana"
    )


class StartEindBase:
    """
    Basis van alle classes met een begin- en einddatum.
    """

    def __init__(self, start: str, einde: str = None):
        """
        Sla de datum stings op als datetime objecten

        Parameters
        ----------
        start: str
            Startdatum is verplicht
        einde: str or None
            Einddatum is optioneel.
        """
        self.start = parse_date(start)
        self.einde = parse_date(einde)


class Vakantie(StartEindBase):
    def __init__(self, start, einde=None, werknemer=None):
        super().__init__(start, einde)

        if werknemer is None:
            self.pool = gantt
        else:
            self.pool = werknemer

        self.add_vacation()

    def add_vacation(self):
        """
        Voeg de gemeenschappelijke vakantiedagen toe
        """
        self.pool.add_vacations(self.start, self.einde)


class Medewerker:
    def __init__(self, label, volledige_naam=None, vakantie_lijst=None):
        self.label = label
        self.volledige_naam = volledige_naam
        self.resource = gantt.Resource(name=label, fullname=volledige_naam)

        if vakantie_lijst is not None:
            self.vakanties = voeg_vakanties_medewerker_toe(
                medewerker=self.resource, vakantie_lijst=vakantie_lijst
            )
        else:
            self.vakanties = None


class BasicElement(StartEindBase):
    def __init__(
        self,
        label,
        start=None,
        afhankelijk_van=None,
        kleur=None,
        volledige_naam=None,
        detail=False,
        display=True,
        opmerking=None,
    ):
        super().__init__(start, start)
        if label is None:
            raise ValueError("Iedere taak moet een label hebben!")
        self.label = label
        self.detail = detail
        self.afhankelijk_van = afhankelijk_van
        self.kleur = color_to_hex(kleur)
        self.volledige_naam = volledige_naam
        self.display = display

        self.opmerking = opmerking


class Taak(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        einde=None,
        duur=None,
        medewerkers=None,
        afhankelijk_van=None,
        kleur=None,
        volledige_naam=None,
        percentage_voltooid=None,
        detail=False,
        display=True,
        deadline=None,
        zwaartepunt=None,
        dvz=None,
        cci=None,
        opmerking=None,
    ):
        super().__init__(
            label=label,
            start=start,
            afhankelijk_van=afhankelijk_van,
            kleur=kleur,
            detail=detail,
            volledige_naam=volledige_naam,
            display=display,
            opmerking=opmerking,
        )
        self.einde = parse_date(einde)
        self.duur = duur
        self.medewerkers = medewerkers
        self.percentage_voltooid = percentage_voltooid

        self.element = None

        # extra velden die je toe kan voegen
        self.deadline = parse_date(deadline, deadline)
        self.zwaartepunt = zwaartepunt
        self.dvz = dvz
        self.cci = cci

        self.voeg_taak_toe()

    def voeg_taak_toe(self):
        self.element = gantt.Task(
            name=self.label,
            start=self.start,
            stop=self.einde,
            duration=self.duur,
            depends_of=self.afhankelijk_van,
            resources=self.medewerkers,
            color=self.kleur,
            percent_done=self.percentage_voltooid,
        )

        self.element.deadline = self.deadline
        self.element.zwaartepunt = self.zwaartepunt
        self.element.dvz = self.dvz
        self.element.cci = self.cci
        self.element.opmerking = self.opmerking


class Mijlpaal(BasicElement):
    def __init__(
        self,
        label,
        start=None,
        afhankelijk_van=None,
        kleur=None,
        detail=False,
        volledige_naam=None,
        display=True,
        opmerking=None,
    ):
        super().__init__(
            label=label,
            start=start,
            afhankelijk_van=afhankelijk_van,
            kleur=kleur,
            detail=detail,
            volledige_naam=volledige_naam,
            display=display,
            opmerking=opmerking,
        )

        self.element = None

        self.voeg_mijlpaal_toe()

    def voeg_mijlpaal_toe(self):
        self.element = gantt.Milestone(
            name=self.label,
            start=self.start,
            depends_of=self.afhankelijk_van,
            color=self.kleur,
        )
        self.element.opmerking = self.opmerking


class ProjectPlanner:
    def __init__(
        self,
        programma_titel=None,
        programma_kleur=None,
        output_file_name=None,
        planning_start=None,
        planning_einde=None,
        vandaag=None,
        schaal=None,
        periode_info=None,
        excel_info=None,
        details=None,
    ):
        self.periode_info = periode_info
        self.planning_start = planning_start
        self.planning_einde = planning_einde
        self.datum_vandaag = vandaag
        self.schaal = schaal
        self.details = details

        self.excel_info = excel_info

        if output_file_name is None:
            self.output_file_name = Path("gantt_projects.svg")
        else:
            self.output_file_name = Path(output_file_name)

        # het hoofdproject maken we alvast aan.
        self.programma = gantt.Project(
            name=programma_titel, color=color_to_hex(programma_kleur)
        )

        self.project_taken = dict()
        self.vakanties = dict()
        self.medewerkers = dict()
        self.taken_en_mijlpalen = dict()
        self.subprojecten = dict()

    @staticmethod
    def maak_globale_informatie():
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
                column_widths=self.excel_info.get("kolombreedtes"),
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
            hangt_af_van = self.taken_en_mijlpalen[key]
            if key in self.subprojecten.keys():
                _logger.warning(
                    f"De afhankelijkheid {key} komt in zowel taken en mijlpalen als in subprojecten voor"
                )
            _logger.debug(f"Afhankelijk van taak of mijlpaal: {key}")
        except KeyError:
            try:
                hangt_af_van = self.subprojecten[key]
                _logger.debug(f"Afhankelijk van project: {key}")
            except KeyError:
                raise AssertionError(f"Afhankelijkheid {key} bestaat niet")

        return hangt_af_van

    def get_medewerkers(self, medewerkers: Union[str, list]) -> list:
        """
        Zet een lijst van medewerkers strings om in een lijst van medewerkers gannt.Resource objecten

        Parameters
        ----------
        medewerkers: list of str
            Lijst van medewerkers of, in het geval er maar 1 medewerker is, een string

        Returns
        -------
        list:
            Lijst van medewerkers resource objecten.

        """

        medewerkers_elementen = list()
        if medewerkers is not None:
            if isinstance(medewerkers, str):
                _logger.debug(f"Voeg medewerker toe: {medewerkers}")
                medewerkers_elementen.append(self.medewerkers[medewerkers].resource)
            else:
                for medewerker in medewerkers:
                    _logger.debug(f"Voeg toe medewerker {medewerker}")
                    medewerkers_elementen.append(self.medewerkers[medewerker].resource)
        return medewerkers_elementen

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
                    for taak_key in afhankelijk_items:
                        afhankelijk_van = self.get_afhankelijkheid(taak_key)
                        afhankelijks_elementen.append(afhankelijk_van)
            else:
                for afhankelijk_item in afhankelijkheden:
                    afhankelijk_van = self.get_afhankelijkheid(afhankelijk_item)
                    afhankelijks_elementen.append(afhankelijk_van)

            return afhankelijks_elementen

    def maak_vakanties(self, vakanties_info):
        """
        Voeg alle algemene vakanties toe
        """
        # Change font default

        # voeg de algemene vakanties toe
        _logger.info("Voeg algemene vakantiedagen toe")
        for v_key, v_prop in vakanties_info.items():
            if v_prop.get("einde") is not None:
                _logger.debug(
                    f"Vakantie {v_key} van {v_prop['start']} to {v_prop.get('einde')}"
                )
            else:
                _logger.debug(f"Vakantie {v_key} op {v_prop['start']}")
            self.vakanties[v_key] = Vakantie(
                start=v_prop["start"], einde=v_prop.get("einde")
            )

    def maak_medewerkers(self, medewerkers_info):
        """
        Voeg de medewerkers met hun vakanties toe.
        """
        _logger.info("Voeg medewerkers toe")
        for w_key, w_prop in medewerkers_info.items():
            _logger.debug(f"Voeg {w_key} ({w_prop.get('naam')}) toe")
            self.medewerkers[w_key] = Medewerker(
                label=w_key,
                volledige_naam=w_prop.get("naam"),
                vakantie_lijst=w_prop.get("vakanties"),
            )

    def maak_taak_of_mijlpaal(
        self, taak_eigenschappen: dict = None
    ) -> Union[Taak, Mijlpaal]:
        """
        Voeg alle algemene taken en mijlpalen toe

        Parameters
        ----------
        taak_eigenschappen:

        Returns
        -------

        """
        afhankelijkheden = self.get_afhankelijkheden(
            taak_eigenschappen.get("afhankelijk_van")
        )
        element_type = taak_eigenschappen.get("type", "taak")
        if element_type == "taak":
            medewerkers = self.get_medewerkers(taak_eigenschappen.get("medewerkers"))
            _logger.debug(f"Voeg taak {taak_eigenschappen.get('label')} toe")
            taak_of_mijlpaal = Taak(
                label=taak_eigenschappen.get("label"),
                start=taak_eigenschappen.get("start"),
                einde=taak_eigenschappen.get("einde"),
                duur=taak_eigenschappen.get("duur"),
                kleur=taak_eigenschappen.get("kleur"),
                detail=taak_eigenschappen.get("detail", False),
                medewerkers=medewerkers,
                afhankelijk_van=afhankelijkheden,
                deadline=taak_eigenschappen.get("deadline"),
                zwaartepunt=taak_eigenschappen.get("zwaartepunt"),
                dvz=taak_eigenschappen.get("dvz"),
                cci=taak_eigenschappen.get("cci"),
                opmerking=taak_eigenschappen.get("opmerking"),
            )
        elif element_type == "mijlpaal":
            _logger.debug(f"Voeg mijlpaal {taak_eigenschappen.get('label')} toe")
            taak_of_mijlpaal = Mijlpaal(
                label=taak_eigenschappen.get("label"),
                start=taak_eigenschappen.get("start"),
                kleur=taak_eigenschappen.get("kleur"),
                afhankelijk_van=afhankelijkheden,
                opmerking=taak_eigenschappen.get("opmerking"),
            )
        else:
            raise AssertionError("Type should be 'taak' or 'mijlpaal'")

        return taak_of_mijlpaal

    def maak_taken_en_mijlpalen(
        self, taken_en_mijlpalen=None, taken_en_mijlpalen_info=None
    ):
        """
        Maak alle taken en mijlpalen
        """

        _logger.info("Voeg alle algemene taken en mijlpalen toe")
        if taken_en_mijlpalen_info is not None:
            # We voegen hier een dictionary van taken en mijlpalen toe
            # Die zijn in modules georganiseerd, haal hier het eerste niveau eraf.
            taken_en_mp = dict()
            for module_key, module_values in taken_en_mijlpalen_info.items():
                _logger.debug(f"lezen taken van module {module_key}")
                for task_key, task_val in module_values.items():
                    _logger.debug(f"Processen taak {task_key}")
                    if task_key in taken_en_mp.keys():
                        msg = f"De taak key {task_key} is al eerder gebruikt. Kies een andere naam!"
                        _logger.warning(msg)
                        raise ValueError(msg)
                    taken_en_mp[task_key] = taken_en_mijlpalen_info[module_key][
                        task_key
                    ]
        else:
            taken_en_mp = taken_en_mijlpalen

        for task_key, task_val in taken_en_mp.items():
            _logger.debug(f"Processen taak {task_key}")
            self.taken_en_mijlpalen[task_key] = self.maak_taak_of_mijlpaal(
                taak_eigenschappen=task_val
            )

    def maak_projecten(
        self,
        subprojecten_info,
        subprojecten_titel,
        subprojecten_selectie,
        subprojecten_kleur=None,
    ):
        """
        Maak alle projecten
        """
        medewerker_color = color_to_hex(subprojecten_kleur)
        projecten_medewerker = gantt.Project(
            name=subprojecten_titel, color=medewerker_color
        )

        _logger.info(f"Voeg alle projecten toe van {subprojecten_titel}")
        for project_key, project_values in subprojecten_info.items():
            _logger.info(f"Maak project: {project_values['titel']}")

            project_name = project_values["titel"]

            project_color = color_to_hex(project_values.get("kleur"))

            _logger.debug("Creating project {}".format(project_name))
            project = gantt.Project(name=project_name, color=project_color)

            # deze elementen voegen we toe om later naar excel te kunnen schrijven
            project.vir = project_values.get("vir")
            project.link = project_values.get("link")
            project.casper_project = project_values.get("casper_project")
            project.casper_taak = project_values.get("casper_taak")
            project.projectleider = project_values.get("projectleider")

            if project_key in self.subprojecten.keys():
                msg = f"project {project_key} bestaat al. Kies een andere naam"
                _logger.warning(msg)
                raise ValueError(msg)

            self.subprojecten[project_key] = project

            if taken := project_values.get("taken"):
                if isinstance(taken, list):
                    taken_dict = {k: k for k in taken}
                else:
                    taken_dict = taken

                for task_key, task_val in taken_dict.items():
                    if isinstance(task_val, dict):
                        is_detail = task_val.get("detail", False)
                    else:
                        is_detail = False
                    if not self.details and is_detail:
                        # We hebben details op False staan en dit is een detail, dus sla deze taak over.
                        _logger.info(
                            f"Sla taak {task_key} over omdat het een detail is"
                        )
                        continue

                    _logger.debug("Adding task {}".format(task_key))

                    is_detail = False

                    if isinstance(task_val, str):
                        try:
                            # de taak een taak of een mijlpaal?
                            taak_obj = self.taken_en_mijlpalen[task_val]
                            taak = taak_obj.element
                            is_detail = taak_obj.detail
                        except KeyError:
                            try:
                                # de taak een ander project?
                                taak = self.subprojecten[task_val]
                            except KeyError as err:
                                _logger.warning(f"{err}")
                                raise
                    else:
                        taak_obj = self.maak_taak_of_mijlpaal(
                            taak_eigenschappen=task_val
                        )
                        taak = taak_obj.element
                        is_detail = taak_obj.detail

                    if not self.details and is_detail:
                        _logger.debug(f"skipping taak {task_key} as it is a detail")
                    else:
                        project.add_task(taak)

            self.subprojecten[project_key] = project
            if project_key in subprojecten_selectie:
                projecten_medewerker.add_task(project)

        # voeg nu alle projecten van de medewerker aan het programma toe
        self.programma.add_task(projecten_medewerker)

    def schrijf_planning(
        self,
        planning_output_directory,
        resource_output_directory,
        schrijf_bronnen=False,
        periodes=None,
    ):
        """
        Schrijf de planning naar de output definities.

        Parameters
        ----------
        schrijf_bronnen: bool
            Schrijf de bronnen file
        planning_output_directory: Path
            Output directory van de svg files van de planning
        resource_output_directory: Path
            Output directory van de svg files van de resources
        periodes: list
            Lijst van periodes die we toevoegen. Als None voegen we alles toe
        """

        for periode_key, periode_prop in self.periode_info.items():

            if periodes is not None and periode_key not in periodes:
                _logger.debug(f"Medewerker {periode_key} wordt over geslagen")
                continue

            suffix = self.output_file_name.suffix
            file_base_tasks = "_".join(
                [self.output_file_name.with_suffix("").as_posix(), periode_key, "taken"]
            )
            file_base_resources = file_base_tasks.replace("_taken", "_bronnen")

            planning_output_directory.mkdir(exist_ok=True, parents=True)

            if schrijf_bronnen:
                resource_output_directory.mkdir(exist_ok=True, parents=True)

            file_name = planning_output_directory / Path(file_base_tasks).with_suffix(
                suffix
            )
            file_name_res = resource_output_directory / Path(
                file_base_resources
            ).with_suffix(suffix)

            schaal = periode_prop.get("schaal")
            if schaal is not None:
                scale = SCALES[schaal]
            else:
                scale = self.schaal

            start = parse_date(periode_prop.get("planning_start"), self.planning_start)
            einde = parse_date(periode_prop.get("planning_einde"), self.planning_einde)
            today = parse_date(periode_prop.get("vandaag"), self.datum_vandaag)
            if scale != SCALES["daily"]:
                # voor een schaal anders dan dagelijks wordt de vandaaglijn alleen op zaterdag getekend!
                _logger.debug("Verander datum op dichtstbijzijnde zaterdag")
                _today = today
                today = get_nearest_saturday(today)
                if today != _today:
                    _logger.debug(
                        f"Verander vandaag datum {_today} in dichtstbijzijnde zaterdag {today}"
                    )

            # the planning is a collection of all the projects
            _logger.info(
                f"Schrijf project van {start} tot {einde} met schaal {scale} naar {file_name}"
            )
            self.programma.make_svg_for_tasks(
                filename=file_name.as_posix(),
                start=start,
                end=einde,
                scale=scale,
                today=today,
            )
            _logger.debug("Done")

            if schrijf_bronnen:
                _logger.info(
                    f"Schrijf bronnen van {start} tot {einde} met schaal {scale} naar {file_name_res}"
                )
                self.programma.make_svg_for_resources(
                    filename=file_name_res.as_posix(),
                    start=start,
                    end=einde,
                    scale=scale,
                    today=today,
                )
            _logger.debug("Done")
