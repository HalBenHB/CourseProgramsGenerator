from src.program_printer import list_programs
from src.data_loader import course_parses, load_requirements_from_json
from src.program_generator import generate_programs, possible_programs

requirements = load_requirements_from_json()
courses = course_parses()

if __name__ == '__main__':

    print("Generating possible programs...")
    generate_programs(0, [],requirements, courses)
    print(f"Found {len(possible_programs)} possible programs:")

    limit_results = 5
    filter_func = lambda program: program['total_days'] == 3
    sort_func = None  # lambda program: program['total_days']
    print_wanted = False
    return_wanted = True
    save_txt = "test.txt"
    include_schedule = True

    fetched_programs = list_programs(possible_programs, courses, filter_func=filter_func, sort_func=sort_func,
                                     print_wanted=print_wanted,
                                     return_wanted=return_wanted, save_txt=save_txt, include_schedule=include_schedule,
                                     limit_results=limit_results)
# %%
