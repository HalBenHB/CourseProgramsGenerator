# src/config.py

import os
from datetime import datetime
from operator import itemgetter
import operator

# A mapping from string representations to actual operator functions
SUPPORTED_OPERATORS = {
    '<=': operator.le,
    '>=': operator.ge,
    '=': operator.eq,
    '==': operator.eq,
    '<': operator.lt,
    '>': operator.gt,
    '!=': operator.ne
}


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
        self.sort_key = kwargs.get('sort_key', "total_days")
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

    def _build_filter_function(self):
        """
        Programmatically builds a filter function and its description string
        without using eval().
        """
        # A list to hold individual filter functions (lambdas)
        filters = []
        # A list to hold human-readable descriptions of the active filters
        descriptions = []

        # --- 1. Day Condition Filter ---
        if self.day_conditions and self.day_conditions[0]:
            condition_str = self.day_conditions[0].strip()
            # Find the operator by checking for 2-char operators first
            op_str = next((op for op in ['<=', '>=', '==', '!='] if op in condition_str), None)
            if not op_str: # If not a 2-char op, check for 1-char op
                op_str = next((op for op in ['<', '>', '='] if op in condition_str), None)

            if op_str and op_str in SUPPORTED_OPERATORS:
                try:
                    value = int(condition_str.replace(op_str, ''))
                    op_func = SUPPORTED_OPERATORS[op_str]

                    # Create the actual function for this filter
                    filters.append(lambda p, op=op_func, v=value: op(p['total_days'], v))
                    descriptions.append(f"Total days {op_str} {value}")
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse day condition '{condition_str}'. Skipping this filter.")

        # --- 2. Exclude Courses Filter ---
        if self.exclude_courses:
            # Using sets is much more efficient for membership testing
            exclude_set = set(self.exclude_courses)
            # A program is valid if its course set is disjoint from the exclude set
            filters.append(lambda p, es=exclude_set: es.isdisjoint(p['courses']))
            descriptions.append(f"Excluding courses: {', '.join(self.exclude_courses)}")

        # --- 3. Include Courses Filter (At least one) ---
        if self.include_courses:
            include_set = set(self.include_courses)
            # A program is valid if its course set is NOT disjoint (i.e., has an intersection)
            filters.append(lambda p, inc_s=include_set: not inc_s.isdisjoint(p['courses']))
            descriptions.append(f"Including at least one of: {', '.join(self.include_courses)}")

        # --- 4. Must Have Courses Filter (All of them) ---
        if self.must_courses:
            must_set = set(self.must_courses)
            # A program is valid if the 'must_set' is a subset of the program's course set
            filters.append(lambda p, ms=must_set: ms.issubset(p['courses']))
            descriptions.append(f"Must include all: {', '.join(self.must_courses)}")

        # --- Combine all active filters into a single function ---
        if not filters:
            # If no filters are active, return a function that always passes
            return (lambda program: True, "None")

        def final_filter(program):
            # The program passes if ALL individual filter functions return True
            program_courses_set = set(program['courses'])
            # We pass a modified program object with a pre-calculated set for efficiency
            program_with_set = {**program, 'courses': program_courses_set}
            return all(f(program_with_set) for f in filters)

        return (final_filter, " and ".join(descriptions))


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

        # --- NEW: Build filter function and description programmatically ---
        filter_func, filter_desc = self._build_filter_function()

        # In the GUI, you now pass a simple key like "total_days" or "total_credits"
        sort_func = itemgetter(self.sort_key) if self.sort_key else None

        self.output = {
            "limit_results": self.limit_number_of_programs,
            "filter_function": filter_func,
            "filter_description": filter_desc,
            "sort_function": sort_func,
            "sort_description": self.sort_key,
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