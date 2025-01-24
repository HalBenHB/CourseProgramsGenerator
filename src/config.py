import os
from datetime import datetime

generation = {
    "min_credit": 30,
    "max_credit": 42,
    "load_programs_from_file": True,  # Default to generating, change to True to load
    "save_programs_to_file": False,  # Default to saving, keep True to save after generation
}

exclude_courses = None#["CS 447.A", "MGMT 311.A"]
include_courses = ["BUS 301.A", "BUS 302.A"]

exclude_condition = "(" + " and ".join(
    [f'"{course}" not in program["courses"]' for course in exclude_courses]) + ")" if exclude_courses else False
include_condition = "(" + " or ".join(
    [f'"{course}" in program["courses"]' for course in include_courses]) + ")" if include_courses else False

conditions = []
conditions.append(exclude_condition) if exclude_condition else None
conditions.append(include_condition) if include_condition else None
filter_condition_str = " and ".join(conditions) if conditions else None

sort_condition_str = "x['total_days']"

output = {
    "limit_results": None,
    "filter_function": eval(f"lambda program: {filter_condition_str}") if filter_condition_str else None,
    "filter_description": filter_condition_str,
    "sort_function": eval(f"lambda x: {sort_condition_str}") if sort_condition_str else None,
    "sort_description": sort_condition_str,
    "print_output": False,
    "return_output": True,
    "save_file": True,
    "include_schedule": True
}

DATA_FOLDER = "data"
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
COURSES_FILENAME = "course_offered_2425F.xls"
REQUIREMENTS_FILENAME = "requirements_test.json"

if output["save_file"]:
    output["save_file"] = os.path.join(DATA_FOLDER, OUTPUT_FOLDER,
                                       datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
else:
    output["save_file"] = False

generation["programs_file_path"] = os.path.join(DATA_FOLDER, INPUT_FOLDER,
                                                f"possible_programs_{generation['min_credit']}-{generation['max_credit']}.pkl")
