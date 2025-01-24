import pandas as pd
import json
import os
from src import config
import pickle

from src.course_models import CourseSection, Course
from src.requirements_model import FullCourseCodeCandidate, CourseIdCandidate, Requirement

COURSES_FILEPATH = os.path.join(config.DATA_FOLDER, config.INPUT_FOLDER, config.COURSES_FILENAME)
REQUIREMENTS_FILEPATH = os.path.join(config.DATA_FOLDER, config.INPUT_FOLDER, config.REQUIREMENTS_FILENAME)


def load_requirements_from_json():
    """Loads requirements from a JSON file."""
    try:
        with open(REQUIREMENTS_FILEPATH, 'r', encoding='utf-8') as f:
            requirements_data = json.load(f)
        return requirements_data
    except FileNotFoundError:
        print(f"Error: Requirements file not found at '{REQUIREMENTS_FILEPATH}'.")
        return None  # Or raise an exception if you prefer
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{REQUIREMENTS_FILEPATH}'.")
        return None  # Or raise an exception


def course_parses(requirements=None):
    # Load the Excel workbook
    df = pd.read_excel(COURSES_FILEPATH)

    courses = {}
    for index, row in df.iterrows():
        subject_code = str(row['SUBJECT']).strip() if pd.notna(row['SUBJECT']) else None
        course_no = str(row['COURSENO']).strip() if pd.notna(row['COURSENO']) else None
        section_no = str(row['SECTIONNO']).strip() if pd.notna(row['SECTIONNO']) else None
        full_course_code = f"{subject_code} {course_no}.{section_no}"
        if requirements:
            if full_course_code not in [candidate_course for candidate_course in
                                        [requirement["candidates"] for requirement in requirements]]:
                pass
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


def load_possible_programs(file_path):
    """Loads possible programs from a pickle file."""
    try:
        with open(file_path, 'rb') as f:
            possible_programs = pickle.load(f)
        print(f"Loaded programs from '{file_path}'.")  # Keep print for info
        return possible_programs
    except FileNotFoundError:
        print(f"File not found: '{file_path}'. No programs loaded.")
        return None  # Indicate no programs loaded, not an error in loading itself
    except Exception as e:  # Catch other potential loading errors
        print(f"Error loading programs from '{file_path}': {e}")
        return None


def save_possible_programs(programs, file_path):
    """Saves possible programs to a pickle file."""
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(programs, f)
        print(f"Programs saved to '{file_path}'.")  # Keep print for info
        return True  # Indicate success
    except Exception as e:
        print(f"Error saving programs to '{file_path}': {e}")
        return False  # Indicate failure
