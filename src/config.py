import os
from datetime import datetime


# Set requirements
requirements_parameter = "requirements_olcay.json"

# Set generation parameters here
min_credit = 29
max_credit = 42
load_programs_if_saved = True
save_programs_after_generation = True

#Set output filter and sort functions here
limit_number_of_programs = 5
day_conditions = None #["<5"]
exclude_courses = None #["CS 447.A"]
include_courses = None #["BUS 302.A"]
must_courses = None  # ["CS 333.A"]
sort_condition_str = "program['total_days']"

#Set output parameters
print_output = False
save_output = True

#config
generation = {
    "min_credit": min_credit,
    "max_credit": max_credit,
    "load_programs_from_file": load_programs_if_saved,  # Default to generating, change to True to load
    "save_programs_to_file": save_programs_after_generation,  # Default to saving, keep True to save after generation
}

day_condition = "(" + " and ".join(
    f'program["total_days"] {day_cond}' for day_cond in day_conditions) + ")" if day_conditions else False
exclude_condition = "(" + " and ".join(
    [f'"{course}" not in program["courses"]' for course in exclude_courses]) + ")" if exclude_courses else False
include_condition = "(" + " or ".join(
    [f'"{course}" in program["courses"]' for course in include_courses]) + ")" if include_courses else False
must_condition = "(" + " and ".join(
    [f'"{course}" in program["courses"]' for course in must_courses]) + ")" if must_courses else False

conditions = []
conditions.append(day_condition) if day_condition else None
conditions.append(exclude_condition) if exclude_condition else None
conditions.append(include_condition) if include_condition else None
conditions.append(must_condition) if must_condition else None
filter_condition_str = " and ".join(conditions) if conditions else None

sort_reverse = False

output = {
    "limit_results": limit_number_of_programs,
    "filter_function": eval(f"lambda program: {filter_condition_str}") if filter_condition_str else None,
    "filter_description": filter_condition_str,
    "sort_function": eval(f"lambda program: {sort_condition_str}") if sort_condition_str else None,
    "sort_description": sort_condition_str,
    "sort_reverse": sort_reverse,
    "print_output": print_output,
    "return_output": True,
    "save_file": save_output,
    "include_schedule": True
}

DATA_FOLDER = "data"
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
COURSES_FILENAME = "course_offered_2425F.xls"
REQUIREMENTS_FILENAME = requirements_parameter

if output["save_file"]:
    output["save_file"] = os.path.join(DATA_FOLDER, OUTPUT_FOLDER,
                                       datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
else:
    output["save_file"] = False

generation["programs_file_path"] = os.path.join(DATA_FOLDER, INPUT_FOLDER,
                                                f"possible_programs_{REQUIREMENTS_FILENAME.replace('.json','')}-min_{generation['min_credit']}-max_{generation['max_credit']}.pkl")
