import pandas as pd
import json
import os
import pickle
import hashlib
from src.course_models import CourseSection

# --- NEW: Helper function to get a file's hash for validation ---
def _get_file_hash(filepath):
    """Computes the MD5 hash of a file for cache validation."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def parse_courses_from_excel(filepath):
    """Parses the raw course data from a given Excel file."""
    df = pd.read_excel(filepath)
    courses = {}

    for _, row in df.iterrows():
        subject_code = str(row['SUBJECT']).strip() if pd.notna(row['SUBJECT']) else ''
        course_no = str(row['COURSENO']).strip() if pd.notna(row['COURSENO']) else ''
        section_no = str(row['SECTIONNO']).strip() if pd.notna(row['SECTIONNO']) else ''
        full_course_code = f"{subject_code} {course_no}.{section_no}"
        course_id = f"{subject_code} {course_no}"

        title = str(row['TITLE']).strip() if pd.notna(row['TITLE']) else None
        faculty = str(row['FACULTY']).strip() if pd.notna(row['FACULTY']) else None
        ects_credits = row['CREDITS'] if pd.notna(row['CREDITS']) else None
        instructor_full_name = str(row['INSTRUCTORFULLNAME']).strip() if pd.notna(row['INSTRUCTORFULLNAME']) else None
        corequisites = str(row['COREQUISITE']).strip() if pd.notna(row['COREQUISITE']) else None
        prerequisites = str(row['PREREQUISITE']).strip() if pd.notna(row['PREREQUISITE']) else None
        description = str(row['DESCRIPTION']).strip() if pd.notna(row['DESCRIPTION']) else None
        schedule_for_print = str(row['SCHEDULEFORPRINT']).strip() if pd.notna(row['SCHEDULEFORPRINT']) else None

        corequisite_list = [coreq for coreq in corequisites.split(" and ")] if corequisites else []

        schedule_list = []
        if schedule_for_print:
            for time_slots in schedule_for_print.split("\n"):
                day, interval = time_slots.split(" | ")
                interval = interval.replace(":", ".")
                schedule_list.append({"day": day, "interval": interval})

        section = CourseSection(full_course_code=full_course_code,
                                ects_credits=int(ects_credits) if pd.notna(ects_credits) else 0,
                                schedule=schedule_list,
                                section_no=section_no, course_name=title, course_id=course_id,
                                subject_code=subject_code, course_number=course_no, faculty=faculty,
                                instructor_full_name=instructor_full_name, corequisites=corequisite_list,
                                prerequisites=prerequisites, description=description)
        courses[full_course_code] = section

    return courses

# --- NEW: Main function to handle the course caching layer ---
def load_and_parse_courses(config_obj):
    """
    Loads all offered courses. Uses a cache for speed if the source file hasn't changed.
    Returns a dictionary of all CourseSection objects.
    """
    courses_filepath = config_obj.input["courses"]["filepath"]
    base_name = os.path.splitext(os.path.basename(courses_filepath))[0]
    cache_filename = f"cache_courses_{base_name}.pkl"
    cache_filepath = os.path.join(config_obj.paths["cache_dir"], cache_filename)

    current_file_hash = _get_file_hash(courses_filepath)

    # Try to load from the course cache
    if os.path.exists(cache_filepath):
        try:
            with open(cache_filepath, 'rb') as f:
                cached_data = pickle.load(f)
            # Validate that the source file has not changed
            if cached_data.get('hash') == current_file_hash:
                print("Course cache is valid. Loading all courses from cache.")
                return cached_data['courses']
            else:
                print("Course cache is stale (source file changed). Re-parsing.")
        except Exception as e:
            print(f"Could not load course cache ({e}). Re-parsing.")

    # Cache miss or stale: Parse the Excel file from scratch
    print("Parsing all courses from Excel file... (This may take a moment on first run)")
    all_courses = parse_courses_from_excel(courses_filepath)

    # Save the newly parsed data to the cache for next time
    try:
        data_to_save = {'hash': current_file_hash, 'courses': all_courses}
        with open(cache_filepath, 'wb') as f:
            pickle.dump(data_to_save, f)
        print(f"Saved parsed course data to cache: '{cache_filename}'")
    except Exception as e:
        print(f"Error saving course data to cache: {e}")

    return all_courses

# --- This function remains the same ---
def load_requirements_from_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Requirements file not found at '{filepath}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filepath}'.")
        return None

# --- The rest of the file (load/save_possible_programs) is unchanged ---
def load_possible_programs(file_path):
    try:
        with open(file_path, 'rb') as f: data = pickle.load(f)
        return data
    except (FileNotFoundError, EOFError): return None
    except Exception as e:
        print(f"Error loading programs from '{file_path}': {e}")
        return None

# --- MODIFIED --- This function now saves the programs along with metadata
def save_possible_programs(programs, file_path, requirements, min_credit, max_credit):
    """Saves possible programs along with their generation metadata to a pickle file."""

    data_to_save = {
        "metadata": {"requirements": requirements, "credits": (min_credit, max_credit)},
        "programs": programs
    }

    try:
        with open(file_path, 'wb') as f: pickle.dump(data_to_save, f)
        print(f"Programs and metadata saved to '{os.path.basename(file_path)}'.")
        return True
    except Exception as e:
        print(f"Error saving programs to '{file_path}': {e}")
        return False