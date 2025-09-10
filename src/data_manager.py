import pandas as pd
import json
import os
from src import config
import pickle

from src.course_models import CourseSection, Course

def load_requirements_from_json():
    requirements_filepath = config.REQUIREMENTS_FILEPATH

    """Loads requirements from a JSON file."""
    try:
        with open(requirements_filepath, 'r', encoding='utf-8') as f:
            requirements_data = json.load(f)
        return requirements_data
    except FileNotFoundError:
        print(f"Error: Requirements file not found at '{requirements_filepath}'.")
        return None  # Or raise an exception if you prefer
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{requirements_filepath}'.")
        return None  # Or raise an exception


def course_parses(requirements=None):

    courses_filepath = config.COURSES_FILEPATH


    # Load the Excel workbook
    df = pd.read_excel(courses_filepath)

    courses = {}

    if requirements:
        candidate_courses = [candidate_course for candidate_courses_list in
                         [requirement["candidates"] for requirement in requirements] for candidate_course in
                         candidate_courses_list]
    for index, row in df.iterrows():
        subject_code = str(row['SUBJECT']).strip() if pd.notna(row['SUBJECT']) else None
        course_no = str(row['COURSENO']).strip() if pd.notna(row['COURSENO']) else None
        section_no = str(row['SECTIONNO']).strip() if pd.notna(row['SECTIONNO']) else None
        full_course_code = f"{subject_code} {course_no}.{section_no}"
        if requirements:
            if full_course_code not in candidate_courses:
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