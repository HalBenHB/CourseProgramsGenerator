from src.program_generator import time_to_minutes


def format_program_info(program, courses, include_schedule):
    program_output = f"\nProgram {program['program_index']}:\n"  # Assuming you will add program_index when calling this
    program_output += "Courses:"
    for course_code in program['courses']:
        program_output += f" {course_code} |"
    program_output += "\n"
    program_output += f"Total Credits: {program['total_credits']}\n"
    program_output += f"Total Days: {program['total_days']}\n"
    program_output += f"Total Hours: {program['total_hours']:.2f}\n"

    if include_schedule:
        program_output += format_program_schedule(program, courses)  # Call helper for schedule formatting

    return program_output


def format_program_schedule(program, courses):
    schedule_output = "Weekly Schedule:\n"
    schedule_by_day = {}
    for course_code in program['courses']:
        course_data = courses[course_code]
        for time_slot in course_data.schedule:
            day = time_slot['day']
            interval = time_slot['interval']
            if day not in schedule_by_day:
                schedule_by_day[day] = []
            schedule_by_day[day].append({
                'interval': interval,
                'course_code': course_code,
                'course_name': course_data.course_name})

    day_order = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    time_slots_display = [
        "08.40-09.30", "09.40-10.30", "10.40-11.30", "11.40-12.30", "12.40-13.30",
        "13.40-14.30", "14.40-15.30", "15.40-16.30", "16.40-17.30", "17.40-18.30",
        "18.40-19.30", "19.40-20.30", "20.40-21.30", "21.40-22.30"
    ]
    time_slots_minutes = [time_to_minutes(slot.split('-')[0].replace(':', '.')) for slot in
                          time_slots_display]

    calendar_grid = {day: [""] * len(time_slots_display) for day in day_order}  # Initialize empty grid

    for day in day_order:
        if day in schedule_by_day:
            for entry in schedule_by_day[day]:
                start_minute = time_to_minutes(entry['interval'].split('-')[0].replace('.', '.'))
                end_minute = time_to_minutes(entry['interval'].split('-')[1].replace('.', '.'))

                start_slot_index = -1
                end_slot_index = -1

                for index, slot_minute in enumerate(time_slots_minutes):
                    if slot_minute <= start_minute < slot_minute + 60:  # Assuming hourly slots
                        start_slot_index = index
                    if slot_minute < end_minute <= slot_minute + 60:
                        end_slot_index = index + 1  # Exclusive end

                if start_slot_index != -1 and end_slot_index != -1:
                    for slot_index in range(start_slot_index, end_slot_index):
                        if 0 <= slot_index < len(time_slots_display):  # Safety check for index range
                            calendar_grid[day][slot_index] = entry['course_code']  # Put course code in slot

    schedule_output += format_calendar_grid(calendar_grid, day_order,
                                            time_slots_display)  # Call helper for grid printing
    return schedule_output


def format_calendar_grid(calendar_grid, day_order, time_slots_display):
    grid_output = ""
    grid_output += "---------------------------------------------------------------------\n"
    grid_output += "| {:<10}".format("Time")  # Time column header
    for day in day_order:
        grid_output += "| {:<10}".format(day)  # Day column headers
    grid_output += "|\n"
    grid_output += "---------------------------------------------------------------------\n"

    for time_index, time_slot in enumerate(time_slots_display):
        grid_output += "| {:<10}".format(time_slot)  # Time slot label
        for day in day_order:
            course_code = calendar_grid[day][time_index]
            grid_output += "| {:<10}".format(course_code)  # Course code or empty slot
        grid_output += "|\n"
    grid_output += "---------------------------------------------------------------------\n"
    return grid_output


def list_programs(programs, courses, filter_function=None, sort_function=None, print_wanted=None, return_wanted=None,
                  save_txt=None, include_schedule=None, limit_results=None, filter_description=None,
                  sort_description=None):
    output_text = ""  # Initialize an empty string to store the output

    summarized_programs = programs
    if filter_function:
        summarized_programs = list(filter(filter_function, summarized_programs))
        output_text += "Filter functions: " + filter_description + "\n"
        print(f"Filtered. Remained {len(summarized_programs)} programs")

    if sort_function:
        summarized_programs = list(sorted(summarized_programs, key=sort_function, reverse=True))
        output_text += "Sorted by: " + sort_description + "\n"
        print(f"Sorted by: {sort_description}")

    if print_wanted or save_txt:  # Include schedule in the condition
        output_text += "Total programs: " + str(len(summarized_programs)) + "\n"
        for i, program in enumerate(summarized_programs):
            program_index = i+1
            if limit_results and limit_results < program_index:
                break
            program_with_index = program.copy()  # To avoid modifying original program
            program_with_index["program_index"] = program_index  # Add program index for output
            program_output = format_program_info(program_with_index, courses, include_schedule)
            output_text += program_output  # Append to the output string
            print('\r'+f'Output generated: {program_index}', end='')


        if print_wanted:  # Print to console if print_wanted is True
            print(program_output, end="")  # print without adding extra newline as program_output already has

        if save_txt:  # Save to text file if save_txt is provided
            try:
                with open(save_txt, 'w', encoding='utf-8') as f:  # Added encoding for broader character support
                    f.write(output_text)
                print(f"\nPrograms saved to '{save_txt}'")  # Inform user that file is saved
            except Exception as e:
                print(f"Error saving to '{save_txt}': {e}")  # Handle potential file writing errors

    if return_wanted:
        return summarized_programs
