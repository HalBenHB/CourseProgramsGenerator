from src.program_printer import list_programs
from src.data_manager import course_parses, load_requirements_from_json, save_possible_programs, load_possible_programs
from src.program_generator import generate_programs
from src import config
import os

# Set requirements
config.requirements_parameter = "requirements.json"

# Set generation parameters here
config.min_credit = 29
config.max_credit = 42
config.load_programs_if_saved = True
config.save_programs_after_generation = True

# Set output filter and sort functions here
config.limit_number_of_programs = 5
config.day_conditions = None  # ["<5"]
config.exclude_courses = None  # ["CS 447.A"]
config.include_courses = None  # ["BUS 302.A"]
config.must_courses = None  # ["CS 333.A"]
config.sort_condition_str = "program['total_days']"

# Set output parameters
config.print_output = False
config.save_output = True


# main.py
config.update_config()
requirements = load_requirements_from_json()
courses = course_parses(requirements)

if __name__ == '__main__':
    programs_file = config.generation["programs_file_path"]

    # Load
    if config.generation["load_programs_from_file"] and os.path.exists(programs_file):
        print(f"Loading possible programs from '{programs_file}'...")
        possible_programs = load_possible_programs(programs_file)

    else:  # Generate
        print("Generating possible programs...")
        possible_programs = generate_programs(requirements, courses, config.generation["min_credit"],
                                              config.generation["max_credit"])
        print(f"Found {len(possible_programs)} possible programs:")

        if config.generation["save_programs_to_file"]:
            print(f"Saving possible programs to '{programs_file}'...")
            save_successful = save_possible_programs(possible_programs, programs_file)

    fetched_programs = list_programs(possible_programs, courses,
                                     filter_function=config.output["filter_function"],
                                     sort_function=config.output["sort_function"],
                                     print_wanted=config.output["print_output"],
                                     return_wanted=config.output["return_output"],
                                     save_txt=config.output["save_file"],
                                     include_schedule=config.output["include_schedule"],
                                     limit_results=config.output["limit_results"],
                                     filter_description=config.output["filter_description"],
                                     sort_description=config.output["sort_description"],
                                     sort_reverse=config.output["sort_reverse"])
