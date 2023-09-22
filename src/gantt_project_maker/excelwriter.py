import logging

import pandas as pd
from pandas.io.formats.excel import ExcelFormatter

import gantt_project_maker.gantt as gantt
from gantt_project_maker.colors import color_to_hex

_logger = logging.getLogger(__name__)

PAGE_WIDTH = 100
CHAR_PER_LINE = 112


class WorkBook:
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
        self.add_styles()

    def add_styles(self):
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


def update_width(label: str, max_width):
    width = len(label)
    if width > max_width:
        max_width = width
    return max_width


def spacing(n_char=5):
    return " " * n_char


def indent(string, n_char=5):
    return spacing(n_char=n_char) + string


def write_planning_to_excel(excel_file, project, header_info, column_widths):
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:

        try:
            projects_per_employee = project.tasks
        except AttributeError as err:
            raise AttributeError(
                f"{err}\nproject heeft helemaal geen tasks. Hier gaat what fout"
            )
        else:
            for projecten_employee in projects_per_employee:
                write_project_to_excel(
                    project=projecten_employee,
                    writer=writer,
                    sheet_name=projecten_employee.name,
                    header_info=header_info,
                    column_widths=column_widths,
                )


def write_project_to_excel(
    project,
    writer,
    sheet_name,
    header_info=None,
    column_widths=None,
    character_width=1.0,
):
    """
    Schrijf een multi index data frame naar Excel file met format

    Parameters
    ----------
    column_widths: dict
        Fix width of these columns.
    header_info: dict
        Information on the header
    project:
        Hoofdproject
    writer: obj
    sheet_name: str
        De sheet name
    character_width: float
        Width of 1 character. Default = 0.7

    """

    ExcelFormatter.header_style = None

    table_df = pd.DataFrame(data=[sheet_name])
    table_df.to_excel(
        writer, sheet_name=sheet_name, startrow=0, header=False, index=False
    )

    worksheet = writer.sheets[sheet_name]
    # worksheet.screen_gridlines = False
    workbook = writer.book

    wb = WorkBook(workbook=workbook)

    write_header(
        header_info=header_info,
        workbook=workbook,
        worksheet=worksheet,
        character_width=character_width,
        wb=wb,
        column_widths=column_widths,
    )

    row_index = 2
    level = 0

    _, level = write_project(
        project,
        header_info=header_info,
        workbook=workbook,
        worksheet=worksheet,
        character_width=character_width,
        wb=wb,
        row_index=row_index,
        level=level,
    )


def write_project(
    project, header_info, workbook, worksheet, character_width, wb, row_index, level
):
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
                    label = ""
                    try:
                        year_start = pd.Timestamp(project.start).year
                    except AttributeError:
                        year_start = ""
                    else:
                        year_start = str(year_start)[-2:]
                    label += f"{year_start}"
                    try:
                        quarter_start = pd.Timestamp(project.start).quarter
                    except AttributeError:
                        quarter_start = ""
                    else:
                        label += f"Q{quarter_start}"
                    try:
                        year_end = pd.Timestamp(project.stop).year
                    except AttributeError:
                        year_end = ""
                    else:
                        year_end = str(year_end)[-2:]
                    try:
                        quarter_end = pd.Timestamp(project.stop).quarter
                    except AttributeError:
                        pass
                    else:
                        if quarter_end != quarter_start or year_start != year_end:
                            label += f"/{year_end}Q{quarter_end}"
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


def write_header(header_info, workbook, worksheet, character_width, wb, column_widths):
    row_index = 0
    col_index = 0
    # begin met tabel nummer op eerste regel en title op regel 2
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
