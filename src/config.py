import os
from datetime import datetime

generation = {
    "min_credit"             : 0,
    "max_credit"             : 999,
    "load_programs_from_file": False,  # Default to generating, change to True to load
    "save_programs_to_file"  : True,  # Default to saving, keep True to save after generation
}

output = {
    "limit_results"   : None,
    "filter_function" : None, #lambda program: program['total_days'] == 3,
    "sort_function"   : None,
    "print_output"    : False,
    "return_output"   : True,
    "save_file"       : True,
    "include_schedule": True
}

DATA_FOLDER = "data"
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
COURSES_FILENAME = "Courses.xlsx"
REQUIREMENTS_FILENAME = "requirements.json"



if output["save_file"]:
    output["save_file"] = os.path.join(DATA_FOLDER, OUTPUT_FOLDER,
                                       datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
else:
    output["save_file"] = False

generation["programs_file_path"] = os.path.join(DATA_FOLDER, INPUT_FOLDER,
                                                f"possible_programs_{generation['min_credit']}-{generation['max_credit']}.pkl")
