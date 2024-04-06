"""
Functions and classes for writing the Excel fiels
"""

import logging

from typing import Union

import pandas as pd
from pandas.io.formats.excel import ExcelFormatter

import gantt_project_maker.gantt as gantt
from gantt_project_maker.colors import color_to_hex
from gantt_project_maker.utils import is_valid_date, is_valid_number, is_valid_int

_logger = logging.getLogger(__name__)

PAGE_WIDTH = 100
CHAR_PER_LINE = 112


class WorkBook:
    """
    A class to hold all the Excel styles

    Args:
        workbook: the Excel workbook to work on
    Attributes:
        workbook:  workbook
        left_align_italic: None
        left_align_italic_large:  None
        left_align_italic_large_ul:  None
        left_align_helvetica:  None
        left_align_helvetica_bold:  None
        left_align_bold:  None
        left_align_bold_large:  None
        left_align:  None
        left_align_large_wrap:  None
        left_align_large_wrap_top:  None
        left_align_wrap:  None
        left_align_large:  None
        right_align:  None
        header_format:  None
        title_format:  None
        section_heading:  None
        footer_format:  None
        merge_format:  None
        date_format:  None
        number_format:  None

    Methods:
        add_styles: function to add the styles
    """

    def __init__(self, workbook):
        self.workbook = workbook
        self.left_align_italic = None
        self.left_align_italic_large = None
        self.left_align_italic_large_ul = None
        self.left_align_helvetica = None
        self.left_align_helvetica_bold = None
        self.left_align_bold = None
        self.left_align_bold_large = None
        self.left_align_bold_larger = None
        self.left_align = None
        self.left_align_large_wrap = None
        self.left_align_large_wrap_top = None
        self.left_align_wrap = None
        self.left_align_large = None
        self.right_align = None
        self.header_format = None
        self.title_format = None
        self.section_heading = None
        self.footer_format = None
        self.merge_format = None
        self.date_format = None
        self.number_format = None
        self.number_format_bold = None
        self.add_styles()

    def add_styles(self):
        """
        Add the Excel styles to the workbook
        """
        self.left_align_helvetica = self.workbook.add_format(
            {"font": "helvetica", "align": "left", "font_size": 8, "border": 0}
        )
        self.left_align_helvetica_bold = self.workbook.add_format(
            {
                "font": "helvetica",
                "bold": True,
                "align": "left",
                "font_size": 8,
                "border": 0,
            }
        )
        self.left_align_italic = self.workbook.add_format(
            {
                "font": "arial",
                "italic": True,
                "align": "left",
                "font_size": 8,
                "border": 0,
            }
        )
        self.left_align_italic_large = self.workbook.add_format(
            {
                "font": "arial",
                "italic": True,
                "align": "left",
                "font_size": 10,
                "border": 0,
            }
        )
        self.left_align_italic_large_ul = self.workbook.add_format(
            {
                "font": "arial",
                "italic": True,
                "align": "left",
                "underline": True,
                "font_size": 10,
                "border": 0,
            }
        )
        self.left_align_bold = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "align": "left",
                "font_size": 8,
                "border": 0,
            }
        )
        self.left_align_bold_large = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "align": "left",
                "font_size": 10,
                "border": 0,
            }
        )
        self.left_align_bold_larger = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "align": "left",
                "font_size": 12,
                "border": 0,
            }
        )
        self.left_align = self.workbook.add_format(
            {"font": "arial", "align": "left", "font_size": 8, "border": 0}
        )
        self.left_align_large_wrap = self.workbook.add_format(
            {
                "font": "arial",
                "align": "left",
                "text_wrap": True,
                "font_size": 10,
                "border": 0,
            }
        )
        self.left_align_large_wrap_top = self.workbook.add_format(
            {
                "font": "arial",
                "align": "left",
                "valign": "top",
                "text_wrap": True,
                "font_size": 10,
                "border": 0,
            }
        )
        self.left_align_large = self.workbook.add_format(
            {"font": "arial", "align": "left", "font_size": 10, "border": 0}
        )
        self.right_align = self.workbook.add_format(
            {"font": "arial", "align": "right", "font_size": 8, "border": 0}
        )
        self.header_format = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "italic": True,
                "text_wrap": True,
                "align": "left",
                "font_size": 8,
            }
        )
        self.header_format.set_bottom()
        self.header_format.set_top()

        self.title_format = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "italic": False,
                "text_wrap": True,
                "align": "centre",
                "font_size": 12,
            }
        )
        self.section_heading = self.workbook.add_format(
            {
                "font": "arial",
                "bold": True,
                "italic": True,
                "text_wrap": True,
                "align": "left",
                "font_size": 11,
            }
        )

        self.footer_format = self.workbook.add_format(
            {
                "font": "arial",
                "align": "left",
                "font_size": 8,
            }
        )
        self.footer_format.set_top()
        self.merge_format = self.workbook.add_format(
            {"border": 1, "align": "center", "valign": "vcenter"}
        )

        self.date_format = self.workbook.add_format(
            {
                "num_format": "dd-mm-yyyy",
                "font": "arial",
                "align": "left",
                "font_size": 8,
                "border": 0,
            }
        )

        self.number_format = self.workbook.add_format(
            {
                "num_format": "General",
                "font": "arial",
                "align": "right",
                "font_size": 8,
                "border": 0,
            }
        )

        self.number_format_bold = self.workbook.add_format(
            {
                "num_format": "General",
                "bold": True,
                "font": "arial",
                "align": "right",
                "font_size": 8,
                "border": 0,
            }
        )


def update_width(label: str, max_width):
    """
    Update the width of a label based on the current maximum width

    Args:
        label (str): Current label
        max_width (int): Current maximum width of the labels

    Returns:
        int: New maximum width
    """
    width = len(label)
    if width > max_width:
        max_width = width
    return max_width


def spacing(n_char=5):
    """
    Create a spacing of n_char characters

    Args:
        n_char (int): Number of white spaces

    Returns:
        str: string of n_char spaces

    """
    return " " * n_char


def indent(line, n_char=5):
    """
    Add an indent with white spaces at the beginning of the line

    Args:
        line (str): line to add a spacing to
        n_char (int):  Number of spaces to add

    Returns:
        str: line with added spacing at the start of the line
    """
    return spacing(n_char=n_char) + line


def write_value_to_named_cell(
    writer: type(pd.ExcelWriter),
    sheet_name: str,
    header_info: dict,
    row_index: int,
    value: int,
    column_key: str,
    cell_format: str = None,
):
    """
    Write a line with the number of hours to the Excel file

    Args:
        writer (obj): Excel writer
        sheet_name (str): Name of the sheet
        header_info (dict): Information on the header
        row_index (int): start writing at this row
        value (str): Number of hours to write to the 'hours' column
        column_key (str): write to this column
        cell_format (str): format of the column
    """

    ExcelFormatter.header_style = None
    try:
        worksheet = writer.sheets[sheet_name]
    except KeyError:
        table_df = pd.DataFrame()
        table_df.to_excel(writer, sheet_name=sheet_name, header=False, index=False)
        worksheet = writer.sheets[sheet_name]

    # worksheet.screen_gridlines = False
    workbook = writer.book

    wb = WorkBook(workbook=workbook)

    if cell_format is not None:
        cell_format: str = getattr(wb, cell_format)
    else:
        cell_format: str = wb.left_align

    col_index = 0
    for info_key, info_val in header_info.items():
        columns_names = info_val["columns"]
        for current_key, column_name in columns_names.items():
            if column_key == current_key:
                _logger.debug(f"Writing hours {column_key}")
                worksheet.write(row_index, col_index, value, cell_format)
            col_index += 1


def write_project_to_excel(
    project: type(gantt.Project),
    writer: type(pd.ExcelWriter),
    sheet_name: str,
    resource: type(gantt.Resource) = None,
    header_info: dict = None,
    column_widths: dict = None,
    character_width: float = 1.0,
    row_index: int = 0,
    header: bool = True,
):
    """
    Write a multi index data frame to Excel file with format

    Args:
        project (dict): Main project
        writer (obj): Excel writer
        sheet_name (str): Name of the sheet
        resource (obj): Resource to filter on. If none, do not filter
        column_widths (dict): Fix width of these columns.
        header_info (dict): Information on the header
        character_width (float): Width of one character. Default = 0.7
        row_index (int): start writing at this row
        header (bool): write the header,
    """

    ExcelFormatter.header_style = None

    try:
        worksheet = writer.sheets[sheet_name]
    except KeyError:
        table_df = pd.DataFrame()
        table_df.to_excel(writer, sheet_name=sheet_name, header=False, index=False)
        worksheet = writer.sheets[sheet_name]

    # worksheet.screen_gridlines = False
    workbook = writer.book

    wb = WorkBook(workbook=workbook)

    if header:
        row_index = write_header(
            header_info=header_info,
            workbook=workbook,
            worksheet=worksheet,
            character_width=character_width,
            wb=wb,
            column_widths=column_widths,
            row_index=row_index,
        )

    level = 0
    total_hours = None

    row_index, level, total_hours = write_project(
        project,
        header_info=header_info,
        workbook=workbook,
        worksheet=worksheet,
        character_width=character_width,
        wb=wb,
        row_index=row_index,
        level=level,
        resource=resource,
        total_hours=total_hours,
    )

    return row_index, level, total_hours


def write_project(
    project: type(gantt.Project),
    header_info: dict,
    workbook: type(WorkBook),
    resource: type(gantt.Resource),
    worksheet,
    character_width: float,
    wb,
    row_index: int,
    level: int,
    total_hours: Union[int, None] = None,
):
    """
    Write the project to a sheet

    Args:
        project (Project): The gantt chart project
        header_info (dict): The header of the Excel file
        workbook (WorkBook): The Excel workbook
        resource (Resource): if given, filter tasks on resource
        worksheet (Worksheet): The Excel worksheet
        character_width (float): The width of the fixed columns
        wb (object): The workbook object to
        row_index (int): The index of the current row
        level (int): The level of the indent
        total_hours (int, optional): Total of hours written on this project so ware

    Returns:
        row_index, level, total_hours: current row index, current project level, current total hours so fare

    """
    _logger.debug("Writing project")
    col_index = 0
    resource_index = 0

    if level == 1:
        row_index += 1

    task_label = None
    write_task = False
    hours = None
    for info_key, info_val in header_info.items():
        _logger.debug(f"Adding project {info_key}")
        columns_names = info_val["columns"]
        for column_key, column_name in columns_names.items():
            _logger.debug(f"Adding column {column_key}")
            try:
                label = getattr(project, column_key)
            except AttributeError:
                # If the column has no attribute, then just go to the next one
                label = None
            if type(project) in (gantt.Task, gantt.Milestone):
                if column_key == "name":
                    task_label = label
                    label = None
                elif column_key == "task":
                    label = task_label
                elif column_key == "hours":
                    try:
                        # store number of hours for current employee
                        label = project.employees[resource.name]
                    except AttributeError:
                        _logger.debug(
                            "project does not have employees or is not a dict"
                        )
                    except KeyError:
                        _logger.debug(
                            f"project has employees but not for {project.name}"
                        )
                    except TypeError:
                        _logger.debug(
                            f"project has employees are stored as a list, so no hours are available for {project.name}"
                        )
                    else:
                        if label is not None:
                            if not is_valid_number(label):
                                _logger.warning(
                                    f"Number of hours '{label}' given in {project.name} is not valid!"
                                )
                            else:
                                if not is_valid_int(label):
                                    _logger.warning(
                                        f"Number of hours '{label}' given in {project.name} is not an integer. Casting "
                                    )
                                hours = int(label)
                elif column_key.startswith("employee"):
                    try:
                        employee = project.get_resources()[resource_index]
                    except IndexError:
                        label = None
                    else:
                        label = employee.name
                        resource_index += 1
                elif column_key == "period":
                    label = project_to_period_label(project=project)

            if label is not None:
                _logger.debug(f"Writing {column_key} with {label}")
                if col_index == 0 and level < 2:
                    formaat = wb.left_align_bold
                elif column_key == "hours":
                    formaat = wb.number_format
                elif is_valid_date(label):
                    formaat = wb.date_format
                else:
                    formaat = wb.left_align

                if resource is not None:
                    write_the_task = is_contributor(project=project, resource=resource)
                else:
                    write_the_task = True

                if write_the_task:
                    worksheet.write(row_index, col_index, label, formaat)
                    write_task = True

            col_index += 1

    if write_task:
        row_index += 1
        if hours is not None:
            if total_hours is None:
                total_hours = 0
            total_hours += hours

    try:
        tasks = project.tasks
    except AttributeError:
        _logger.debug("This is a task, so does not have tasks ")
    else:
        for task in tasks:
            level += 1
            row_index, level, total_hours = write_project(
                task,
                header_info=header_info,
                workbook=workbook,
                worksheet=worksheet,
                character_width=character_width,
                wb=wb,
                row_index=row_index,
                level=level,
                resource=resource,
                total_hours=total_hours,
            )

    level -= 1
    return row_index, level, total_hours


def is_contributor(project, resource, is_contributing=False):
    """
    check if resource is contributor of the project
    Args:
        project:
        resource:
        is_contributing: bool
    Returns:

    """
    if is_contributing:
        return is_contributing

    try:
        employees = project.employees
    except AttributeError:
        pass
    else:
        if isinstance(employees, str):
            is_contributing = resource.name == employees
        elif isinstance(employees, dict):
            is_contributing = resource.name in employees.keys()
        else:
            is_contributing = resource.name in employees
        if is_contributing:
            return is_contributing

    try:
        tasks = project.tasks
    except AttributeError:
        pass
    else:
        for task in tasks:
            is_contributing = is_contributor(project=task, resource=resource)
            if is_contributing:
                return True

    return is_contributing


def write_header(
    header_info, workbook, worksheet, character_width, wb, column_widths, row_index
):
    """
    Write the header of a Excel sheet

    Args:
        header_info (dict):  The header infor of this sheet
        workbook (WorkBook): The Excel workbook
        worksheet (str): The name of the sheet
        character_width (float): The width of the characters
        wb (workbook): The object to the workbook
        column_widths (dict): The columns widths for this sheet
        row_index (int): start writing at this row
    """
    col_index = 0
    # Start with the table number on first line and title on the second line
    for info_key, info_val in header_info.items():
        _logger.debug(f"Adding header for {info_key}")
        columns_names = info_val["columns"]
        title = info_val["title"]
        n_columns = len(columns_names.keys())
        if cell_color := info_val.get("color"):
            color = color_to_hex(cell_color)
        else:
            color = "black"

        merge_format = workbook.add_format(
            {
                "bold": True,
                "border": 6,
                "align": "center",
                "valign": "vcenter",
                "fg_color": color,
            }
        )
        if n_columns > 1:
            first_col = col_index
            last_col = col_index + n_columns - 1
            _logger.debug(
                f"Merging cells {first_col} - {last_col} at ro {row_index}: {title} {color}"
            )
            worksheet.merge_range(
                row_index, first_col, row_index, last_col, title, merge_format
            )
        else:
            _logger.debug(f"Writing cell {col_index}  at ro {row_index}: {title}")
            worksheet.write(row_index, col_index, title, merge_format)

        for column_key, column_name in columns_names.items():
            _logger.debug(f"Adding column {column_key}")
            worksheet.write(row_index + 1, col_index, column_name, wb.left_align_bold)

            column_width = len(column_name)
            if column_widths is not None:
                for col_key, col_width in column_widths.items():
                    if col_key == column_key:
                        column_width = col_width
            worksheet.set_column(col_index, col_index, column_width * character_width)
            col_index += 1

    # we have written 2 rows, so skip two
    row_index += 2
    return row_index


def project_to_period_label(project: type(gantt.Project)) -> str:
    """
    Take the start and end dates of the project and convert to a period label, like 24Q1 (first quarter of 2024) or
    24Q324Q4 (third and last quarter of 2024)


    Args:
        project (Project): Project class with start_date and  end_date methods

    Returns:
        str: label of the period, such as 24Q3 or 24Q3/25Q1
    """
    label = ""
    try:
        year_start = pd.Timestamp(project.start).year
    except AttributeError:
        year_start = ""
    else:
        year_start = str(year_start)[-2:]
    label += f"{year_start}"
    try:
        quarter_start = pd.Timestamp(project.start_date()).quarter
    except AttributeError:
        quarter_start = ""
    else:
        label += f"Q{quarter_start}"
    try:
        year_end = pd.Timestamp(project.end_date()).year
    except AttributeError:
        year_end = ""
    else:
        year_end = str(year_end)[-2:]
    try:
        quarter_end = pd.Timestamp(project.end_date()).quarter
    except AttributeError:
        pass
    else:
        if quarter_end != quarter_start or year_start != year_end:
            label += f"/{year_end}Q{quarter_end}"
    return label


def write_resource(
    project: type(gantt.Project),
    header_info: dict,
    workbook: type(WorkBook),
    worksheet,
    character_width: float,
    wb,
    row_index: int,
    level: int,
):
    """
    Write the project to a sheet

    Args:
        project (Project): The gantt chart project
        header_info (dict): The header of the Excel file
        workbook (WorkBook): The Excel workbook
        worksheet (Worksheet): The Excel worksheet
        character_width (float): The width of the fixed columns
        wb (object): The workbook object to
        row_index (int): The index of the current row
        level (int): The level of the indent

    Returns:

    """
    _logger.debug("Writing project")
    col_index = 0
    resource_index = 0

    if level == 1:
        row_index += 1

    task_label = None
    for info_key, info_val in header_info.items():
        _logger.debug(f"Adding project {info_key}")
        columns_names = info_val["columns"]
        for column_key, column_name in columns_names.items():
            _logger.debug(f"Adding column {column_key}")

            try:
                label = getattr(project, column_key)
            except AttributeError:
                # als de kolom geen attribute heeft dan gewoon naar de volgende
                label = None
            if type(project) in (gantt.Task, gantt.Milestone):
                if column_key == "name":
                    task_label = label
                    label = None
                elif column_key == "task":
                    label = task_label
                elif column_key.startswith("employee"):
                    try:
                        employee = project.get_resources()[resource_index]
                    except IndexError:
                        label = None
                    else:
                        label = employee.name
                        resource_index += 1
                elif column_key == "period":
                    label = project_to_period_label(project=project)

            if label is not None:
                _logger.debug(f"Writing {column_key} with {label}")
                try:
                    dummy = label.strftime("%d-%m-%Y")
                except AttributeError:
                    is_date = False
                else:
                    is_date = True
                    _logger.debug(f"Label is a date with format {dummy}")
                if col_index == 0 and level < 2:
                    formaat = wb.left_align_bold
                elif is_date:
                    formaat = wb.date_format
                else:
                    formaat = wb.left_align

                worksheet.write(row_index, col_index, label, formaat)
            col_index += 1

    row_index += 1

    try:
        tasks = project.tasks
    except AttributeError:
        _logger.debug("This is a task, so does not have tasks ")
    else:
        for task in tasks:
            level += 1
            row_index, level = write_project(
                task,
                header_info=header_info,
                workbook=workbook,
                worksheet=worksheet,
                character_width=character_width,
                wb=wb,
                row_index=row_index,
                level=level,
            )

    level -= 1
    return row_index, level


def project_to_period_label(project: type(gantt.Project)) -> str:
    """
    Take the start and end dates of the project and convert to a period label, like 24Q1 (first quarter of 2024) or
    24Q324Q4 (third and last quarter of 2024)


    Args:
        project (Project): Project class with start_date and  end_date methods

    Returns:
        str: label of the period, such as 24Q3 or 24Q3/25Q1
    """
    label = ""
    try:
        year_start = pd.Timestamp(project.start).year
    except AttributeError:
        year_start = ""
    else:
        year_start = str(year_start)[-2:]
    label += f"{year_start}"
    try:
        quarter_start = pd.Timestamp(project.start_date()).quarter
    except AttributeError:
        quarter_start = ""
    else:
        label += f"Q{quarter_start}"
    try:
        year_end = pd.Timestamp(project.end_date()).year
    except AttributeError:
        year_end = ""
    else:
        year_end = str(year_end)[-2:]
    try:
        quarter_end = pd.Timestamp(project.end_date()).quarter
    except AttributeError:
        pass
    else:
        if quarter_end != quarter_start or year_start != year_end:
            label += f"/{year_end}Q{quarter_end}"
    return label
