import operator


def check_satisfied(needed, count):
    # Define a dictionary to map operators to their corresponding functions
    condition_operators = {
        "=" : operator.eq,
        "<=": operator.le,
        ">=": operator.ge,
        "<" : operator.lt,
        ">" : operator.gt
    }

    # Extract the operator and value
    for op in condition_operators.keys():
        if needed.startswith(op):
            value = int(
                needed[len(op):])  # Extract the number after the operator
            condition_func = condition_operators[op]
            return condition_func(count, value)
    raise ValueError(f"Invalid condition: {needed}")


# Helper function to convert a time string to a datetime object (for comparison)
def time_to_minutes(time_str) -> int:
    """Convert time in 'HH.MM' format to total minutes"""
    hours, minutes = map(int, time_str.split("."))
    return hours * 60 + minutes


# Helper function to convert a time string to a datetime object (for comparison)
def minutes_to_time(minutes_int) -> str:
    hours, minutes = divmod(minutes_int, 60)
    hours = str(hours)
    minutes = str(minutes)
    if len(hours) == 1:
        hours = "0" + hours
    if len(minutes) == 1:
        minutes = "0" + minutes
    return hours + '.' + minutes


# Helper function to parse the schedule string
def parse_time_slot(time_slot_str):
    """Parse a schedule string and return a list of (day, start_time, end_time) tuples"""
    day = time_slot_str["day"]
    start_time, end_time = time_slot_str["interval"].split("-")
    return day, time_to_minutes(start_time), time_to_minutes(end_time)


# Helper function to check if two time slots overlap
def check_program_course_conflict(current_program_param, candidate_schedule_param):
    for current_day, current_start, current_end in (parse_time_slot(slot) for slot in
                                                    current_program_param["schedule"]):
        for candidate_day, candidate_start, candidate_end in (parse_time_slot(slot) for slot in
                                                              candidate_schedule_param):
            if candidate_day == current_day:
                if candidate_start < current_end and candidate_end > current_start:
                    return True  # Conflict
    return False  # No conflict


def calculate_program_stats(program, courses):
    """Calculates total days and total hours for a program."""
    days = set()
    total_minutes = 0
    for course_code in program['courses']:
        for schedule_entry in courses[course_code]['schedule']:
            days.add(schedule_entry['day'])
            start_minutes = time_to_minutes(schedule_entry['interval'].split('-')[0])
            end_minutes = time_to_minutes(schedule_entry['interval'].split('-')[1])
            total_minutes += (end_minutes - start_minutes)

    program["total_days"] = len(days)
    program["total_hours"] = total_minutes / 60.0  # Convert minutes to hours
    return program


def is_program_valid(program, requirements, courses, min_credit, max_credit):
    total_credits = sum(int(courses[course_code].ects_credits) for course_code in program['courses'])
    if not (min_credit <= total_credits <= max_credit):
        return False

    for req in requirements:
        count = 0
        for course_code in program['courses']:
            if course_code in req['candidates']:
                count += 1
        if not check_satisfied(req['needed'], count):
            return False

    program["total_credits"] = total_credits
    program = calculate_program_stats(program, courses)  # Calculate total_days and total_hours
    return True


def _generate_programs(requirement_index, current_program_courses, requirements, courses, min_credit, max_credit,
                       possible_programs):
    if requirement_index == len(requirements):
        program = {
            "courses" : current_program_courses,
            "schedule": []
        }
        for course_code in current_program_courses:
            program["schedule"].extend(courses[course_code].schedule)

        if is_program_valid(program, requirements, courses, min_credit, max_credit):
            # print(f"Found valid program: {program}")
            possible_programs.append(program)
        return

    # Option 1: Try to fulfill the requirement with candidates
    current_requirement = requirements[requirement_index]
    course_options = current_requirement["candidates"]
    needed_condition = current_requirement["needed"]

    # Determine how many courses we *can* take for this requirement (based on 'needed')
    max_courses_for_req = float('inf')  # default max is infinity
    if "<=" in needed_condition:
        max_courses_for_req = int(needed_condition.split("<=")[1])
    elif "=" in needed_condition:
        max_courses_for_req = int(needed_condition.split("=")[1])
    elif "<" in needed_condition:
        max_courses_for_req = int(needed_condition.split("<")[1]) - 1
    elif ">=" in needed_condition:
        max_courses_for_req = float('inf')  # actually limited by total program credits/other reqs
    elif ">" in needed_condition:
        max_courses_for_req = float('inf')  # actually limited by total program credits/other reqs

    def generate_combinations_for_requirement(candidate_index, courses_taken_for_req, current_program_courses):
        if courses_taken_for_req > max_courses_for_req:  # Stop if we've taken too many for this requirement
            return

        if candidate_index == len(course_options):  # Reached end of candidates for this requirement
            if check_satisfied(needed_condition, courses_taken_for_req):  # Check if we satisfied the needed condition
                _generate_programs(requirement_index + 1, current_program_courses, requirements,
                                   courses, min_credit, max_credit, possible_programs)  # Move to next requirement
            return

        # Option A: Don't take the current candidate course
        generate_combinations_for_requirement(candidate_index + 1, courses_taken_for_req, current_program_courses)

        # Option B: Take the current candidate course if no conflict
        candidate_course_code = course_options[candidate_index]
        candidate_course = courses[candidate_course_code]
        # Construct current program schedule for conflict check
        current_program_schedule_for_check = {
            "schedule": []}
        for course_code in current_program_courses:
            current_program_schedule_for_check["schedule"].extend(courses[course_code].schedule)

        if not check_program_course_conflict(current_program_schedule_for_check, candidate_course.schedule):
            updated_program_courses = current_program_courses.copy()
            # updated_program_courses[candidate_course_code] = candidate_course
            updated_program_courses.append(candidate_course_code)
            generate_combinations_for_requirement(candidate_index + 1, courses_taken_for_req + 1,
                                                  updated_program_courses)

    generate_combinations_for_requirement(0, 0, current_program_courses.copy())


def generate_programs(requirements, courses, min_credit_param, max_credit_param):
    """
    Generates a list of possible course programs that satisfy the given requirements and credit limits.

    Args:
        requirements: A list of requirement dictionaries.
        courses: A dictionary of course information, keyed by course code.
        min_credit: The minimum total credits for a valid program.
        max_credit: The maximum total credits for a valid program.

    Returns:
        A list of dictionaries, where each dictionary represents a valid course program.
        Each program dictionary contains 'courses' (list of course codes), 'schedule' (combined schedule),
        'total_credits', 'total_days', and 'total_hours'.
    """


    possible_programs = []

    # Defaults
    min_credit = 30 if min_credit_param is None else min_credit_param
    max_credit = 42 if max_credit_param is None else max_credit_param

    _generate_programs(0, [], requirements, courses, min_credit, max_credit, possible_programs)
    return possible_programs
