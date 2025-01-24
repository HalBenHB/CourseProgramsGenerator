#NOT IMPLEMENTED
import abc  # For Abstract Base Classes

class CourseCandidate(abc.ABC):
    """Abstract base class for course candidates in requirements."""

    @abc.abstractmethod
    def matches_course_section(self, course_section):
        """
        Abstract method to check if a course section matches this candidate.

        Args:
            course_section (CourseSection): The CourseSection object to check.

        Returns:
            bool: True if the course section matches, False otherwise.
        """
        pass

    @abc.abstractmethod
    def __repr__(self):
        """Abstract method for string representation."""
        pass


class CourseIdCandidate(CourseCandidate):
    """Represents a course candidate specified by Course ID (subject and number, any section)."""

    def __init__(self, course_id):
        """
        Initializes a CourseIdCandidate.

        Args:
            course_id (str): The Course ID (e.g., "CS 333").
        """
        self.course_id = course_id

    def matches_course_section(self, course_section):
        """
        Checks if the given course section's course_id matches this candidate's course_id.

        Args:
            course_section (CourseSection): The CourseSection object to check.

        Returns:
            bool: True if the course_id matches, False otherwise.
        """
        return course_section.course_id == self.course_id

    def __repr__(self):
        return f"<CourseIdCandidate: {self.course_id}>"


class FullCourseCodeCandidate(CourseCandidate):
    """Represents a course candidate specified by Full Course Code (including section)."""

    def __init__(self, full_course_code):
        """
        Initializes a FullCourseCodeCandidate.

        Args:
            full_course_code (str): The Full Course Code (e.g., "CS 333.A").
        """
        self.full_course_code = full_course_code

    def matches_course_section(self, course_section):
        """
        Checks if the given course section's full_course_code exactly matches this candidate's full_course_code.

        Args:
            course_section (CourseSection): The CourseSection object to check.

        Returns:
            bool: True if the full_course_code matches, False otherwise.
        """
        return course_section.full_course_code == self.full_course_code

    def __repr__(self):
        return f"<FullCourseCodeCandidate: {self.full_course_code}>"


class Requirement:
    """Represents a course requirement."""

    def __init__(self, requirement_name, candidates, needed):
        """
        Initializes a Requirement object.

        Args:
            requirement_name (str): The name of the requirement (e.g., "CS").
            candidates (list): A list of CourseCandidate objects.
            needed (str): Condition string for how many courses are needed (e.g., "=1", "<=2").
        """
        self.requirement_name = requirement_name
        self.candidates = candidates
        self.needed = needed

    def __repr__(self):
        return f"<Requirement: {self.requirement_name} - Needed: {self.needed}, Candidates: {self.candidates}>"