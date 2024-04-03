"""
Some utility functions
"""


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
