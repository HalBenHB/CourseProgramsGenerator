import os
from datetime import datetime

generation = {
    "min_credit"             : 30,
    "max_credit"             : 42,
    "load_programs_from_file": False,  # Default to generating, change to True to load
    "save_programs_to_file"  : True,  # Default to saving, keep True to save after generation
}

output = {
    "limit_results"   : None,
    "filter_function" : lambda program: "CS 447" not in program['courses'] and ("BUS 301" in program['courses'] or "BUS 302" in program['courses']),
    "sort_function"   : lambda x: x['total_days'],
    "print_output"    : False,
    "return_output"   : True,
    "save_file"       : True,
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
