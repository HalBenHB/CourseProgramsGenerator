# src/main.py

from src.program_printer import list_programs
from src.data_manager import course_parses, load_requirements_from_json, save_possible_programs, load_possible_programs
from src.program_generator import generate_programs
from src import config
import os

def run_program_generation(app_config):
    """
    Main logic for generating and listing programs.
    This function is designed to be called from the GUI or other scripts.

    Args:
        app_config (dict): A dictionary containing 'generation' and 'output' settings.

    Returns:
        tuple: (list of program dicts, log string, path of the auto-saved file)

    """
    # Load requirements and courses based on config
    requirements = load_requirements_from_json() # Assumes config.REQUIREMENTS_FILEPATH is set
    if not requirements:
        return [], "Error: Could not load requirements file.", None

    # We now pass the requirements to course_parses to potentially speed it up
    courses = course_parses(requirements=requirements)
    if not courses:
        return [], "Error: Could not parse courses file.", None

    programs_file = app_config["generation"]["programs_file_path"]
    min_credit = app_config["generation"]["min_credit"]
    max_credit = app_config["generation"]["max_credit"]
    output_str = ""

    # --- MODIFIED --- New, robust caching logic
    cache_hit = False
    if app_config["generation"]["load_programs_from_file"] and os.path.exists(programs_file):
        output_str += f"Potential cache file found at '{os.path.basename(programs_file)}'. Validating...\n"
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

        if app_config["generation"]["save_programs_to_file"]:
            output_str += f"Saving possible programs to cache file '{os.path.basename(programs_file)}'...\n"
            # Pass the metadata to be saved with the programs
            save_possible_programs(possible_programs, programs_file, requirements, min_credit, max_credit)

    # Filter, sort, and format the output
    # IMPORTANT: We set print_wanted=False and return_wanted=True to capture the output string
    summarized_programs, formatted_output = list_programs(possible_programs, courses,
                                     filter_function=app_config["output"]["filter_function"],
                                     sort_function=app_config["output"]["sort_function"],
                                     print_wanted=False, # We will display this in the GUI, not print to console
                                     return_wanted=True, # We need the programs and the text output
                                     save_txt=app_config["output"]["save_file"],
                                     include_schedule=app_config["output"]["include_schedule"],
                                     limit_results=app_config["output"]["limit_results"],
                                     filter_description=app_config["output"]["filter_description"],
                                     sort_description=app_config["output"]["sort_description"],
                                     sort_reverse=app_config["output"]["sort_reverse"])

    # If a file was saved, add that info to the output
    if app_config["output"]["save_file"]:
         output_str += f"\nFormatted output also saved to file: {app_config['output']['save_file']}\n"

    output_str += formatted_output
    auto_save_path = app_config["output"]["save_file"]
    return summarized_programs, output_str, auto_save_path


if __name__ == '__main__':
    # This part allows you to still run main.py as a standalone script for testing
    print("Running main.py as a script...")
    config.update_config() # Use default config
    app_config = {"generation": config.generation, "output": config.output}
    results = run_program_generation(app_config)
    print(results)