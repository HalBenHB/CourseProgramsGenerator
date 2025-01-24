class CourseSection:
    """Represents a specific section of a course."""

    def __init__(self, full_course_code, ects_credits, schedule, section_no, course_name, course_id, subject_code, course_number,
                 faculty, instructor_full_name, corequisites, prerequisites, description):
        """
        Initializes a CourseSection object.

        Args:
            full_course_code (str): The full course code including section (e.g., "PSY 325.A").
            section_no (str): The section identifier (e.g., "A").
            course_name (str): The title of the course.
            ects_credits (int): The number of credits for the course section.
            schedule (list): A list of schedule dictionaries (e.g., [{'day': 'Monday', 'interval': '09.00-10.00'}]).
            subject_code (str): The subject code (e.g., "PSY").
            course_number (str): The course number (e.g., "325").
            faculty (str): The faculty offering the course.
            instructor_full_name (str): The full name of the instructor.
            corequisites (list): A list of corequisite course codes.
            prerequisites (str): Prerequisite information string.
            description (str): Course description.
        """

        self.full_course_code = full_course_code
        self.section_no = section_no
        self.course_name = course_name
        self.ects_credits = ects_credits
        self.schedule = schedule
        self.subject_code = subject_code
        self.course_number = course_number
        self.faculty = faculty
        self.instructor_full_name = instructor_full_name
        self.corequisites = corequisites
        self.prerequisites = prerequisites
        self.description = description

    def __repr__(self):
        """Provides a string representation of the CourseSection object (for debugging/printing)."""
        return f"<CourseSection: {self.full_course_code}>"


class Course:
    """Represents a general course (without section), holding multiple CourseSection objects."""

    def __init__(self, course_id, course_name, subject_code, course_number, description, prerequisites, corequisites):
        """
        Initializes a Course object.

        Args:
            course_id (str): The course identifier without section (e.g., "PSY 325").
            course_name (str): The general title of the course.
            subject_code (str): The subject code (e.g., "PSY").
            course_number (str): The course number (e.g., "325").
            description (str): General course description.
            prerequisites (str): General prerequisite information string.
            corequisites (list): General list of corequisite course codes.
        """
        self.course_id = course_id
        self.course_name = course_name
        self.subject_code = subject_code
        self.course_number = course_number
        self.description = description
        self.prerequisites = prerequisites
        self.corequisites = corequisites
        self.sections = {}  # Dictionary to hold CourseSection objects, keyed by section_id

    def add_section(self, section):
        """Adds a CourseSection object to this Course's sections dictionary."""
        if isinstance(section, CourseSection):
            self.sections[section.section_no] = section
        else:
            raise TypeError("Only CourseSection objects can be added as sections.")

    def get_section(self, section_id):
        """Retrieves a CourseSection object by its section_id."""
        return self.sections.get(section_id)

    def get_all_sections(self):
        """Returns a list of all CourseSection objects associated with this Course."""
        return list(self.sections.values())

    def __repr__(self):
        """Provides a string representation of the Course object (for debugging/printing)."""
        return f"<Course: {self.course_id} - {self.course_name}>"