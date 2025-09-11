import pandas as pd
import json
import os
import pickle
from src.course_models import CourseSection

# --- MODIFIED --- Accepts a filepath directly
def load_requirements_from_json(filepath):
    """Loads requirements from the specified JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Requirements file not found at '{filepath}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filepath}'.")
        return None

# --- MODIFIED --- Accepts a filepath directly
def course_parses(filepath, requirements=None):
    df = pd.read_excel(filepath)
    courses = {}

    # --- This optimization logic now works correctly ---
    candidate_courses = set()
    if requirements:
        for req in requirements:
            if 'candidates' in req:
                candidate_courses.update(req['candidates'])

    for _, row in df.iterrows():
        subject_code = str(row['SUBJECT']).strip() if pd.notna(row['SUBJECT']) else ''
        course_no = str(row['COURSENO']).strip() if pd.notna(row['COURSENO']) else ''
        section_no = str(row['SECTIONNO']).strip() if pd.notna(row['SECTIONNO']) else ''
        full_course_code = f"{subject_code} {course_no}.{section_no}"

        if requirements and full_course_code not in candidate_courses:
            continue

        course_id = f"{subject_code} {course_no}"
        title = str(row['TITLE']).strip() if pd.notna(row['TITLE']) else None
        faculty = str(row['FACULTY']).strip() if pd.notna(row['FACULTY']) else None
        ects_credits = row['CREDITS'] if pd.notna(row['CREDITS']) else None
        instructor_full_name = str(row['INSTRUCTORFULLNAME']).strip() if pd.notna(row['INSTRUCTORFULLNAME']) else None
        corequisites = str(row['COREQUISITE']).strip() if pd.notna(row['COREQUISITE']) else None
        prerequisites = str(row['PREREQUISITE']).strip() if pd.notna(row['PREREQUISITE']) else None
        description = str(row['DESCRIPTION']).strip() if pd.notna(row['DESCRIPTION']) else None
        schedule_for_print = str(row['SCHEDULEFORPRINT']).strip() if pd.notna(row['SCHEDULEFORPRINT']) else None

        corequisite_list = [corequisite for corequisite in corequisites.split(" and ")] if corequisites else []

        schedule_list = []
        if schedule_for_print:
            for time_slots in schedule_for_print.split("\n"):
                day, interval = time_slots.split(" | ")
                interval = interval.replace(":", ".")
                start_time, end_time = interval.split(" - ")
                schedule_list.append({
                    "day": day,
                    "interval": interval}
                )

        section = CourseSection(full_course_code=full_course_code,
                                ects_credits=int(ects_credits) if pd.notna(ects_credits) else 0,
                                schedule=schedule_list,
                                section_no=section_no,
                                course_name=title,
                                course_id=course_id,
                                subject_code=subject_code,
                                course_number=course_no,
                                faculty=faculty,
                                instructor_full_name=instructor_full_name,
                                corequisites=corequisite_list,
                                prerequisites=prerequisites,
                                description=description
                                )

        # if course_id not in courses:
        #     # Create a new Course object if it doesn't exist yet
        #     course = Course(
        #         course_id=course_id,
        #         course_name=title,  # General course name
        #         subject_code=subject_code,
        #         course_number=course_no,
        #         description=description,  # General description
        #         prerequisites=prerequisites,  # General prerequisites
        #         corequisites=corequisite_list  # General corequisites
        #     )
        #     courses[course_id] = course  # Add Course object to the courses dictionary

        # courses[course_id].add_section(section)  # Add the CourseSection to the Course object
        courses[full_course_code] = section

    return courses

# --- MODIFIED --- This function now returns the entire data structure
def load_possible_programs(file_path):
    """Loads the entire data structure (metadata and programs) from a pickle file."""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading programs from '{file_path}': {e}")
        return None

# --- MODIFIED --- This function now saves the programs along with metadata
def save_possible_programs(programs, file_path, requirements, min_credit, max_credit):
    """Saves possible programs along with their generation metadata to a pickle file."""

    data_to_save = {
        "metadata": {
            "requirements": requirements,
            "credits": (min_credit, max_credit)
        },
        "programs": programs
    }

    try:
        with open(file_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        print(f"Programs and metadata saved to '{file_path}'.")
        return True
    except Exception as e:
        print(f"Error saving programs to '{file_path}': {e}")
        return False