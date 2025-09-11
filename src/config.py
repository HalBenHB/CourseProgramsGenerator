# src/config.py

import os
from datetime import datetime


class Config:
    """An object to hold all configuration settings for a generation run."""

    def __init__(self, **kwargs):
        """
        Initializes the Config object with base parameters.
        Accepts keyword arguments to override defaults.
        """
        # Base Parameters (can be set by the user/GUI)
        self.courses_parameter = kwargs.get('courses_parameter', "course_offered_2526S.xls")
        self.requirements_parameter = kwargs.get('requirements_parameter', "requirements_halil.json")
        self.min_credit = kwargs.get('min_credit', 30)
        self.max_credit = kwargs.get('max_credit', 42)
        self.limit_number_of_programs = kwargs.get('limit_number_of_programs', 5)
        self.day_conditions = kwargs.get('day_conditions', None)
        self.exclude_courses = kwargs.get('exclude_courses', None)
        self.include_courses = kwargs.get('include_courses', None)
        self.must_courses = kwargs.get('must_courses', None)
        self.sort_condition_str = kwargs.get('sort_condition_str', "program['total_days']")
        self.sort_reverse = kwargs.get('sort_reverse', False)

        # Caching Parameters
        self.load_programs_if_saved = kwargs.get('load_programs_if_saved', True)
        self.save_programs_after_generation = kwargs.get('save_programs_after_generation', True)

        # Output Parameters
        self.save_output = kwargs.get('save_output', True)

        # --- Derived Parameters (will be built by the update() method) ---
        self.generation = {}
        self.output = {}
        self.REQUIREMENTS_FILEPATH = None
        self.COURSES_FILEPATH = None
        self.OUTPUT_FILEPATH = None
        self.INPUT_FILEPATH = None

        # The update() method must be called to build the derived parameters
        # before the config object is used by the backend.

    def update(self):
        """
        Builds the derived configuration values (like full paths and lambda functions)
        based on the base parameters. This should be called after all user settings
        have been applied to the object.
        """
        root_dir = os.path.dirname(os.path.dirname(__file__))
        self.INPUT_FILEPATH = os.path.join(root_dir, "data", "input")
        self.OUTPUT_FILEPATH = os.path.join(root_dir, "data", "output")

        # Build full paths from parameters
        self.REQUIREMENTS_FILEPATH = os.path.join(self.INPUT_FILEPATH, self.requirements_parameter)
        self.COURSES_FILEPATH = os.path.join(self.INPUT_FILEPATH, self.courses_parameter)

        self.generation = {
            "min_credit": self.min_credit,
            "max_credit": self.max_credit,
            "load_programs_from_file": self.load_programs_if_saved,
            "save_programs_to_file": self.save_programs_after_generation,
            # This will be set by the GUI's hash-based generator
            "programs_file_path": None
        }

        # Build filter and sort functions
        day_cond = f'program["total_days"] {self.day_conditions[0]}' if self.day_conditions else None
        exclude_cond = " and ".join(
            [f'"{c}" not in program["courses"]' for c in self.exclude_courses]) if self.exclude_courses else None
        include_cond = " or ".join(
            [f'"{c}" in program["courses"]' for c in self.include_courses]) if self.include_courses else None
        must_cond = " and ".join(
            [f'"{c}" in program["courses"]' for c in self.must_courses]) if self.must_courses else None

        conditions = [c for c in [day_cond, exclude_cond, include_cond, must_cond] if c]
        filter_condition_str = " and ".join(f"({c})" for c in conditions) if conditions else "True"

        self.output = {
            "limit_results": self.limit_number_of_programs,
            "filter_function": eval(f"lambda program: {filter_condition_str}"),
            "filter_description": filter_condition_str if filter_condition_str != "True" else "None",
            "sort_function": eval(f"lambda program: {self.sort_condition_str}") if self.sort_condition_str else None,
            "sort_description": self.sort_condition_str,
            "sort_reverse": self.sort_reverse,
            "return_output": True,
            "save_file": self.save_output,
            "include_schedule": True
        }

        if self.output["save_file"]:
            self.output["save_file"] = os.path.join(self.OUTPUT_FILEPATH,
                                                    datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        else:
            self.output["save_file"] = False


# For any script that needs a simple, default configuration without the GUI
default_config = Config()
default_config.update()