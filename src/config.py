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
        # --- File and Path Parameters ---
        self.paths = {
            "root": None,
            "input_dir": None,
            "output_dir": None,
            "reqs_dir": None,
            "cache_dir": None,
            "pre_reqs_dir": None
        }

        self.input = {
            "courses": {
                "basename": kwargs.get('courses_basename', "course_offered_2526S.xls"),
                "filepath": None
            },
            "requirements": {
                "basename": kwargs.get('requirements_basename', "requirements_halil.json"),
                "filepath": None
            },
            "cache": {
                "enabled": kwargs.get('load_from_cache', True),
                "filepath": None  # Will be set dynamically by the GUI
            }
        }

        self.output = {
            "report": {
                "enabled": kwargs.get('save_report', True),
                "filepath": None
            },
            "cache": {
                "enabled": kwargs.get('save_to_cache', True),
            }
        }

        # --- Generation and Display Parameters ---
        self.generation_params = {
            "min_credit": kwargs.get('min_credit', 30),
            "max_credit": kwargs.get('max_credit', 42),
        }

        self.display_params = {
            "limit_results": kwargs.get('limit_results', 5),
            "include_schedule": True,
            "sort_key": kwargs.get('sort_key', "total_days"),
            "sort_reverse": kwargs.get('sort_reverse', False),
            "filters": {
                "day_conditions": kwargs.get('day_conditions', None),
                "exclude_courses": kwargs.get('exclude_courses', None),
                "include_courses": kwargs.get('include_courses', None),
                "must_courses": kwargs.get('must_courses', None),
            }
        }

        # --- Derived, Processed Functions (built by update()) ---
        self.filter_function = None
        self.filter_description = "None"
        self.sort_function = None

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
        day_conds = self.display_params['filters']['day_conditions']
        if day_conds and day_conds[0]:
            condition_str = self.day_conditions[0].strip()
            # Find the operator by checking for 2-char operators first
            op_str = next((op for op in ['<=', '>=', '==', '!='] if op in condition_str), None)
            if not op_str:  # If not a 2-char op, check for 1-char op
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
        exclude_courses = self.display_params['filters']['exclude_courses']
        if exclude_courses:
            exclude_set = set(exclude_courses)
            filters.append(lambda p, es=exclude_set: es.isdisjoint(p['courses']))
            descriptions.append(f"Excluding courses: {', '.join(exclude_courses)}")

        # --- 3. Include Courses Filter (At least one) ---
        include_courses = self.display_params['filters']['include_courses']
        if include_courses:
            include_set = set(include_courses)
            # A program is valid if its course set is NOT disjoint (i.e., has an intersection)
            filters.append(lambda p, inc_s=include_set: not inc_s.isdisjoint(p['courses']))
            descriptions.append(f"Including at least one of: {', '.join(self.include_courses)}")

        # --- 4. Must Have Courses Filter (All of them) ---
        must_courses = self.display_params['filters']['must_courses']
        if must_courses:
            must_set = set(must_courses)
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
        # --- 1. Set up base paths ---
        self.paths["root"] = os.path.dirname(os.path.dirname(__file__))
        self.paths["input_dir"] = os.path.join(self.paths["root"], "data", "input")
        self.paths["output_dir"] = os.path.join(self.paths["root"], "data", "output")

        # --- NEW: Build full paths for new subdirectories ---
        self.paths["reqs_dir"] = os.path.join(self.paths["input_dir"], "reqs")
        self.paths["cache_dir"] = os.path.join(self.paths["input_dir"], "caches")
        self.paths["pre_reqs_dir"] = os.path.join(self.paths["input_dir"], "pre_reqs")

        # --- NEW (Robustness): Ensure all directories exist ---
        for path in [self.paths["output_dir"], self.paths["reqs_dir"], self.paths["cache_dir"],
                     self.paths["pre_reqs_dir"]]:
            os.makedirs(path, exist_ok=True)

        # --- 2. Build full input file paths ---
        # Main course files are still in the root of input/
        self.input["courses"]["filepath"] = os.path.join(self.paths["input_dir"], self.input["courses"]["basename"])

        # --- CHANGED: Requirement files are now in the 'reqs' subdirectory ---
        self.input["requirements"]["filepath"] = os.path.join(self.paths["reqs_dir"],
                                                              self.input["requirements"]["basename"])

        # --- 3. Build full output file paths ---
        if self.output["report"]["enabled"]:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.output["report"]["filepath"] = os.path.join(self.paths["output_dir"], f"{timestamp}.txt")
        else:
            self.output["report"]["filepath"] = None

        # --- 4. Build filter and sort functions ---
        self.filter_function, self.filter_description = self._build_filter_function()
        sort_key = self.display_params.get("sort_key")
        self.sort_function = itemgetter(sort_key) if sort_key else None


# For any script that needs a simple, default configuration without the GUI
default_config = Config()
default_config.update()
