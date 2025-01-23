from src.program_printer import list_programs
from src.data_loader import course_parses, load_requirements_from_json
from src.program_generator import generate_programs

requirements = load_requirements_from_json()
courses = course_parses()
min_credit = 0
max_credit = 42
possible_programs = []

config = {
    "limit_results"   : None,
    "filter_function" : lambda program: program['total_days'] == 3,
    "sort_function"   : None,
    "print_output"    : False,
    "return_output"   : False,
    "save_file"       : "0-42.txt",  # "test.txt",
    "include_schedule": True
}

if __name__ == '__main__':
    print("Generating possible programs...")
    possible_programs = generate_programs(requirements, courses, min_credit, max_credit)
    print(f"Found {len(possible_programs)} possible programs:")

    fetched_programs = list_programs(possible_programs, courses,
                                     filter_function=config["filter_function"], sort_function=config["sort_function"],
                                     print_wanted=config["print_output"], return_wanted=config["return_output"],
                                     save_txt=config["save_file"], include_schedule=config["include_schedule"],
                                     limit_results=config["limit_results"])
# %%
