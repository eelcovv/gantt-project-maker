"""
Some utility functions
"""

from argparse import ArgumentTypeError
import dateutil.parser as dparse
import logging

_logger = logging.getLogger(__name__)


def get_task_contribution(name, task, owner_id) -> dict:
    """
    Taks contribution

    Args:
        name (str): Name of the task to process.
        task (Task): Task instance
        owner_id (str): Owner key of the task

    Returns:
        dict: task contribution of the resource

    """

    task_contribution = dict()
    for resource_for_task in task.resources:
        if resource_for_task.name == name:
            task_contribution["start"] = task.start
            try:
                task_contribution["stop"] = task.stop
            except AttributeError:
                task_contribution["stop"] = None
            task_contribution[owner_id] = task.owner
            if isinstance(task.employees, dict):
                task_contribution["hours"] = task.employees[name]
            else:
                task_contribution["hours"] = None

    return task_contribution


def is_valid_number(label: str):
    """
    Check is label is a valid number

    Args:
        label (str): label to validate

    Returns:
        bool: True if a valid number
    """

    is_number = True
    try:
        number = float(label)
    except ValueError:
        is_number = False

    return is_number


def is_valid_int(label: str):
    """
    Check is label is a valid integer

    Args:
        label (str): label to validate

    Returns:
        bool: True if a valid number
    """

    is_int = True
    try:
        number = int(label)
    except ValueError:
        is_int = False

    return is_int


def is_valid_date(label: str):
    """
    Check is a label is a valid date

    Args:
        label (str): a string value. In case a number is passed, it is casted into a string

    Returns:
        bool: True if label is a valid date
    """

    label_is_date = True
    try:
        check_if_date(str(label))
    except ArgumentTypeError:
        label_is_date = False

    return label_is_date


def check_if_date(value: str):
    """
    Check if an argument is a valid date
    Args:
        value (str): date/time string

    Returns:
        str: Date/time string

    Raises:
        ArgumentTypeError: raised in case the value string is not a valid date/time string
    """

    try:
        date = dparse.parse(value).date()
    except ValueError:
        raise ArgumentTypeError(f"Date {value} is not a valid date")
    else:
        _logger.debug(f"Date {date} is a valid date")
    return value


def deep_copy_dict(properties: dict) -> dict:
    """
    Create a deep copy of a nested dictionary

    Args:
        properties (dict): The dictionary to copy

    Returns:
        dict: New dictionary with the new values

    """

    new_values = {}

    for key, value in properties.items():
        if isinstance(value, dict):
            new_values[key] = deep_copy_dict(value)
        else:
            new_values[key] = value

    return new_values
