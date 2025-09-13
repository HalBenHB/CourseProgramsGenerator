from src.program_generator import time_to_minutes

def format_program_info(program, courses, include_schedule, loc_manager):
    loc = loc_manager
    program_output = loc.get_string('program_header', index=program['program_index'])
    program_output += loc.get_string('courses_header')
    for course_code in program['courses']:
        program_output += f" {course_code} |"
    program_output += "\n"
    program_output += loc.get_string('total_credits_header', credits=program['total_credits'])
    program_output += loc.get_string('total_days_header', days=program['total_days'])
    program_output += loc.get_string('total_hours_header', hours=program['total_hours'])

    if include_schedule:
        program_output += format_program_schedule(program, courses, loc)  # Call helper for schedule formatting

    return program_output


def format_program_schedule(program, courses, loc_manager):
    loc = loc_manager
    schedule_output = loc.get_string('weekly_schedule_header')
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

    day_order = loc.get_string('day_names')
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
                                            time_slots_display, loc)  # Call helper for grid printing
    return schedule_output


def format_calendar_grid(calendar_grid, day_order, time_slots_display, loc_manager):
    try:
        course_code_len = max(len(course_code) for day in day_order for course_code in calendar_grid[day]) if any(any(d) for d in calendar_grid.values()) else 10
    except ValueError:
        course_code_len = 10 # Default if grid is empty

    grid_output = ""
    separator_length = ((course_code_len + 2) * 5) + 13
    separator = "-" * separator_length + "\n"
    grid_output += separator

    grid_output += "| {:<{}}".format(loc_manager.get_string('time_header'), 11)  # Time column header
    for day in day_order:
        grid_output += "| {:<{}}".format(day, course_code_len)  # Day column headers
    grid_output += "|\n"
    grid_output += separator

    for time_index, time_slot in enumerate(time_slots_display):
        grid_output += "| {:<{}}".format(time_slot, 11)  # Time slot label
        for day in day_order:
            course_code = calendar_grid[day][time_index]
            grid_output += "| {:<{}}".format(course_code, course_code_len)  # Course code or empty slot
        grid_output += "|\n"
    grid_output += separator
    return grid_output


def list_programs(programs, courses, loc_manager, filter_function=None, sort_function=None, print_wanted=None, return_wanted=None,
                  save_txt=None, include_schedule=None, limit_results=None, filter_description=None,
                  sort_description=None, sort_reverse=False, cancel_event=None):
    loc = loc_manager
    output_parts = []
    if cancel_event and cancel_event.is_set():
        return [], "".join(output_parts)

    summarized_programs = programs
    if filter_function:
        summarized_programs = list(filter(filter_function, summarized_programs))
        output_parts.append(loc.get_string('filter_log', desc=filter_description))
        print(f"Filtered. Remained {len(summarized_programs)} programs")

    # --- NEW: Check for cancellation before sorting ---
    if cancel_event and cancel_event.is_set():
        return [], "".join(output_parts)

    if sort_function:
        summarized_programs = sorted(summarized_programs, key=sort_function, reverse=sort_reverse)
        rev_str = " (Descending)" if sort_reverse else ""
        output_parts.append(loc.get_string('sort_log', desc=sort_description, rev=rev_str))
        print(f"Sorted by: {sort_description}" + rev_str)

    output_parts.append(loc.get_string('total_programs_log', count=len(summarized_programs)))

    if print_wanted or save_txt:
        programs_to_print = summarized_programs[:limit_results] if limit_results else summarized_programs
        total_to_process = len(programs_to_print)

        if limit_results:
            output_parts.append(loc.get_string('displaying_top_log', count=min(limit_results, total_to_process)))

        print("\r\r\r")  # A newline before progress bar
        for i, program in enumerate(programs_to_print):
            if cancel_event and cancel_event.is_set():
                output_parts.append(f"Formatting cancelled.\n")
                print("\nFormatting cancelled.")
                # Return what we have formatted so far
                final_output_text = "".join(output_parts)
                # Since we are returning partial results, don't save the incomplete file
                if save_txt:
                    print(f"File not saved to '{save_txt}' due to cancellation.")
                if return_wanted:
                    return summarized_programs, final_output_text
                return None, None

            program["program_index"] = i + 1
            program_output = format_program_info(program, courses, include_schedule, loc)

            output_parts.append(program_output) # Append to the list (very fast)

            # --- THE UI OPTIMIZATION ---
            # Only print a progress update periodically, not on every single iteration.
            # The modulo operator (%) is perfect for this.
            progress_update_number = 100 if total_to_process<=20000 else 1000
            if (i + 1) % progress_update_number == 0 or (i + 1) == total_to_process:
                print(f'\r\nOutput generated: {i + 1}/{total_to_process}', end='', flush=True)

        print() # Final newline after progress bar

    # --- CHANGE 3: Join the list into a single string ONCE at the end ---
    final_output_text = "".join(output_parts)

    if print_wanted:
        # Note: printing a massive string to the console can itself be slow.
        # This is a limitation of the terminal, not the Python script.
        print(final_output_text)

    if save_txt:
        try:
            with open(save_txt, 'w', encoding='utf-8') as f:
                f.write(final_output_text)
            print(f"\nPrograms saved to '{save_txt}'")
        except Exception as e:
            print(f"Error saving to '{save_txt}': {e}")  # Handle potential file writing errors

    if return_wanted:
        if not output_parts:
             final_output_text = ""
        elif 'final_output_text' not in locals():
             final_output_text = "".join(output_parts)

        return summarized_programs, final_output_text

    return None, None