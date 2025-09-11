# src/main.py
from src.program_printer import list_programs
from src.data_manager import course_parses, load_requirements_from_json, save_possible_programs, load_possible_programs
from src.program_generator import generate_programs
from src.config import Config
import os

def run_program_generation(config_obj):
    """
    Main logic for generating and listing programs.
    This function is designed to be called from the GUI or other scripts.

    Args:
        config_obj (Config): A fully updated Config object.

    Returns:
        tuple: (list of program dicts, log string, path of the auto-saved file)

    """
    # Load requirements and courses based on config
    requirements = load_requirements_from_json(config_obj) # Assumes config.REQUIREMENTS_FILEPATH is set
    if not requirements:
        return [], "Error: Could not load requirements file.", None

    # We now pass the requirements to course_parses to potentially speed it up
    courses = course_parses(config_obj, requirements=requirements)
    if not courses:
        return [], "Error: Could not parse courses file.", None

    # Get values directly from the config object's dictionaries
    programs_file = config_obj.generation["programs_file_path"]
    min_credit = config_obj.generation["min_credit"]
    max_credit = config_obj.generation["max_credit"]
    output_str = ""
    possible_programs = []

    # --- MODIFIED --- New, robust caching logic
    cache_hit = False
    if config_obj.generation["load_programs_from_file"] and os.path.exists(programs_file):
        output_str += f"Potential cache file found: '{os.path.basename(programs_file)}'. Validating...\n"
        cached_data = load_possible_programs(programs_file)

        if cached_data and isinstance(cached_data, dict) and 'metadata' in cached_data:
            # Validate if the cached data was generated with the exact same parameters
            metadata = cached_data['metadata']
            if metadata.get('requirements') == requirements and metadata.get('credits') == (min_credit, max_credit):
                output_str += "Cache is valid. Loading programs from cache.\n"
                possible_programs = cached_data['programs']
                cache_hit = True
            else:
                output_str += "Cache is stale (requirements or credit limits differ). Regenerating programs.\n"
        else:
            output_str += "Cache file is invalid or old format. Regenerating programs.\n"

    if not cache_hit:
        output_str += "Generating possible programs... (This may take a while)\n"
        possible_programs = generate_programs(requirements, courses, min_credit, max_credit)
        output_str += f"Found {len(possible_programs)} possible programs.\n"
        if config_obj.generation["save_programs_to_file"]:
            output_str += f"Saving programs to cache file '{os.path.basename(programs_file)}'...\n"
            save_possible_programs(possible_programs, programs_file, requirements, min_credit, max_credit)

    # Filter, sort, and format the output
    # IMPORTANT: We set print_wanted=False and return_wanted=True to capture the output string
    summarized_programs, formatted_output = list_programs(
        programs=possible_programs,
        courses=courses,
                                     filter_function=config_obj.output["filter_function"],
                                     sort_function=config_obj.output["sort_function"],
                                     print_wanted=False, # We will display this in the GUI, not print to console
                                     return_wanted=True, # We need the programs and the text output
                                     save_txt=config_obj.output["save_file"],
                                     include_schedule=config_obj.output["include_schedule"],
                                     limit_results=config_obj.output["limit_results"],
                                     filter_description=config_obj.output["filter_description"],
                                     sort_description=config_obj.output["sort_description"],
                                     sort_reverse=config_obj.output["sort_reverse"])

    auto_save_path = config_obj.output.get("save_file", None)
    if auto_save_path:
        output_str += f"\nFormatted output also saved to file: {auto_save_path}\n"

    output_str += formatted_output
    return summarized_programs, output_str, auto_save_path


if __name__ == '__main__':
    print("Running main.py as a script with default config...")
    # Create an instance and update it for standalone runs
    default_config = Config()
    default_config.update()
    _, results_text, _ = run_program_generation(default_config)
    print(results_text)