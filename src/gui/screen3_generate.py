import os
import json
import sys
import threading
import queue
import shutil
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.main import run_program_generation
from .widgets import Tooltip, StdoutRedirector  # <-- Relative import


class Screen3(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.loc = controller.loc
        self.generation_thread = None
        self.last_auto_save_path = None
        self.cancel_event = threading.Event()
        self.tooltips = {}

        # --- WIDGET CREATION ---
        self.title_label = ttk.Label(self, font=("Helvetica", 16))
        self.title_label.pack(pady=10)

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", expand=True)

        # Generation Parameters Frame
        self.gen_frame = ttk.LabelFrame(top_frame)
        self.gen_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.gen_vars = {
            "min_credit": tk.StringVar(value=self.controller.config.generation_params["min_credit"]),
            "max_credit": tk.StringVar(value=self.controller.config.generation_params["max_credit"]),
            "load_if_possible": tk.BooleanVar(value=self.controller.config.input["cache"]["enabled"])
        }
        self.min_max_label = ttk.Label(self.gen_frame)
        self.min_max_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.gen_frame, textvariable=self.gen_vars["min_credit"], width=5).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(self.gen_frame, textvariable=self.gen_vars["max_credit"], width=5).grid(row=0, column=2, sticky="w", pady=2)
        self.credits_q_label = ttk.Label(self.gen_frame, text="(?)", cursor="question_arrow")
        self.credits_q_label.grid(row=0, column=3, sticky="w", padx=5)
        self.cache_check = ttk.Checkbutton(self.gen_frame, variable=self.gen_vars["load_if_possible"])
        self.cache_check.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        # Output Parameters Frame
        self.out_frame = ttk.LabelFrame(top_frame)
        self.out_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.out_vars = {
            "limit": tk.StringVar(value=self.controller.config.display_params["limit_results"] or ""),
            "sort_str": tk.StringVar(value=self.controller.config.display_params["sort_key"]),
            "sort_reverse": tk.BooleanVar(value=self.controller.config.display_params["sort_reverse"])
        }
        self.limit_label = ttk.Label(self.out_frame)
        self.limit_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.out_frame, textvariable=self.out_vars["limit"], width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.limit_q_label = ttk.Label(self.out_frame, text="(?)", cursor="question_arrow")
        self.limit_q_label.grid(row=0, column=2, sticky="w", padx=5)
        self.sort_label = ttk.Label(self.out_frame)
        self.sort_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.out_frame, textvariable=self.out_vars["sort_str"], width=20).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.sort_desc_check = ttk.Checkbutton(self.out_frame, variable=self.out_vars["sort_reverse"])
        self.sort_desc_check.grid(row=1, column=2, sticky="w")
        self.sort_q_label = ttk.Label(self.out_frame, text="(?)", cursor="question_arrow")
        self.sort_q_label.grid(row=1, column=3, sticky="w", padx=5)

        # Filtering Frame
        self.filter_frame = ttk.LabelFrame(self)
        self.filter_frame.pack(fill="x", padx=5, pady=5)
        self.filter_frame.columnconfigure(1, weight=1)
        self.filter_vars = {"day_num_cond": tk.StringVar(), "exclude": tk.StringVar(), "include": tk.StringVar(), "must": tk.StringVar()}
        self.day_checkbox_vars = {day: tk.IntVar(value=0) for day in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]}

        day_filter_frame = ttk.Frame(self.filter_frame)
        day_filter_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        self.day_cond_label = ttk.Label(day_filter_frame)
        self.day_cond_label.pack(side="left")
        ttk.Entry(day_filter_frame, textvariable=self.filter_vars["day_num_cond"], width=5).pack(side="left", padx=5)
        self.day_num_q_label = ttk.Label(day_filter_frame, text="(?)", cursor="question_arrow")
        self.day_num_q_label.pack(side="left", padx=(0, 20))
        self.day_cbs = {}
        for day, var in self.day_checkbox_vars.items():
            # Create the checkbutton
            cb = ttk.Checkbutton(day_filter_frame, text=day[:2], variable=var)

            # Bind to the mouse click event instead.
            cb.bind("<Button-1>", lambda event, v=var: self._on_day_checkbox_click(event, v))


            cb.pack(side="left", padx=2)
            self.day_cbs[day] = cb

        self.exclude_label = ttk.Label(self.filter_frame)
        self.exclude_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.filter_frame, textvariable=self.filter_vars["exclude"], width=40).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.exclude_q_label = ttk.Label(self.filter_frame, text="(?)", cursor="question_arrow")
        self.exclude_q_label.grid(row=1, column=2, sticky="w", padx=5)

        self.include_label = ttk.Label(self.filter_frame)
        self.include_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.filter_frame, textvariable=self.filter_vars["include"], width=40).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.include_q_label = ttk.Label(self.filter_frame, text="(?)", cursor="question_arrow")
        self.include_q_label.grid(row=2, column=2, sticky="w", padx=5)

        self.must_label = ttk.Label(self.filter_frame)
        self.must_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.filter_frame, textvariable=self.filter_vars["must"], width=40).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.must_q_label = ttk.Label(self.filter_frame, text="(?)", cursor="question_arrow")
        self.must_q_label.grid(row=3, column=2, sticky="w", padx=5)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10)
        self.back_btn = ttk.Button(bottom_frame, command=lambda: controller.show_screen2())
        self.back_btn.pack(side="left")
        button_container = ttk.Frame(bottom_frame)
        button_container.pack(side="right")
        self.generate_btn = ttk.Button(button_container, command=self.start_generation_thread)
        self.generate_btn.pack(side="right")
        self.cancel_btn = ttk.Button(button_container, command=self.cancel_generation, state="disabled")
        self.cancel_btn.pack(side="right", padx=(0, 5))
        self.save_output_btn = ttk.Button(bottom_frame, command=self.save_output, state="disabled")
        self.save_output_btn.pack(side="right", padx=10)

        # Log Frame
        self.log_frame = ttk.LabelFrame(self)
        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_text = tk.Text(self.log_frame, wrap="word", height=15)
        self.output_text.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.pack(fill="y", side="right")
        self.output_text.config(yscrollcommand=scrollbar.set)
        sys.stdout = StdoutRedirector(self.output_text)

        self.update_text()

    def update_text(self):
        """Update all text elements on this screen to the current language."""
        loc = self.loc
        self.title_label.config(text=loc.get_string('screen3_title'))
        self.gen_frame.config(text=loc.get_string('gen_params_label'))
        self.min_max_label.config(text=loc.get_string('min_max_credits_label'))
        self.cache_check.config(text=loc.get_string('load_cached_label'))
        self.out_frame.config(text=loc.get_string('output_params_label'))
        self.limit_label.config(text=loc.get_string('limit_programs_label'))
        self.sort_label.config(text=loc.get_string('sort_by_label'))
        self.sort_desc_check.config(text=loc.get_string('descending_label'))
        self.filter_frame.config(text=loc.get_string('filtering_label'))
        self.day_cond_label.config(text=loc.get_string('day_conds_label'))
        self.exclude_label.config(text=loc.get_string('exclude_courses_label'))
        self.include_label.config(text=loc.get_string('include_one_label'))
        self.must_label.config(text=loc.get_string('must_have_label'))
        self.back_btn.config(text=loc.get_string('back'))
        # Handle button state for generate/cancel
        if self.generate_btn['state'] == 'disabled':
            self.generate_btn.config(text=loc.get_string('generating_btn'))
            self.cancel_btn.config(text=loc.get_string('cancelling_btn') if self.cancel_btn['text'] != loc.get_string('cancel_btn') else loc.get_string('cancel_btn'))
        else:
            self.generate_btn.config(text=loc.get_string('generate_btn'))
            self.cancel_btn.config(text=loc.get_string('cancel_btn'))

        self.save_output_btn.config(text=loc.get_string('save_output_btn'))
        self.log_frame.config(text=loc.get_string('output_log_label'))

        # --- Re-create Tooltips ---
        self.tooltips['credits'] = Tooltip(self.credits_q_label, loc.get_string('credits_tooltip'))
        self.tooltips['cache'] = Tooltip(self.cache_check, loc.get_string('cache_tooltip'))
        self.tooltips['limit'] = Tooltip(self.limit_q_label, loc.get_string('limit_tooltip'))
        self.tooltips['sort'] = Tooltip(self.sort_q_label, loc.get_string('sort_tooltip'))
        self.tooltips['day_num'] = Tooltip(self.day_num_q_label, loc.get_string('day_num_tooltip'))
        self.tooltips['exclude'] = Tooltip(self.exclude_q_label, loc.get_string('exclude_tooltip'))
        self.tooltips['include'] = Tooltip(self.include_q_label, loc.get_string('include_tooltip'))
        self.tooltips['must'] = Tooltip(self.must_q_label, loc.get_string('must_tooltip'))
        for day, cb in self.day_cbs.items():
            self.tooltips[day] = Tooltip(cb, loc.get_string('day_cycle_tooltip', day=day))

    def _generate_cache_filename(self):
        config_obj = self.controller.config
        courses_basename = os.path.splitext(config_obj.input["courses"]["basename"])[0]
        req_string = json.dumps(self.controller.requirements, sort_keys=True, separators=(',', ':'))
        req_hash = hashlib.sha256(req_string.encode('utf-8')).hexdigest()[:16]
        safe_courses_name = "".join(c for c in courses_basename if c.isalnum() or c in (' ', '_')).rstrip()
        min_cred = config_obj.generation_params["min_credit"]
        max_cred = config_obj.generation_params["max_credit"]
        cache_filename = f"cache_{safe_courses_name}_reqs_{req_hash}_cr_{min_cred}-{max_cred}.pkl"
        return os.path.join(config_obj.paths["cache_dir"], cache_filename)


    def save_output(self):
        if not self.last_auto_save_path or not os.path.exists(self.last_auto_save_path):
            messagebox.showwarning(self.loc.get_string('warning'), self.loc.get_string('no_output_found_warning'))
            return
        default_filename = os.path.basename(self.last_auto_save_path)
        destination_path = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".txt",
                                                        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")),
                                                        title="Save Output As")
        if destination_path:
            try:
                shutil.copy(self.last_auto_save_path, destination_path)
                messagebox.showinfo("Success", self.loc.get_string('output_copied_msg', path=destination_path))
            except Exception as e:
                messagebox.showerror(self.loc.get_string('error'), f"Failed to copy file: {e}")

    def start_generation_thread(self):
        self.cancel_event.clear()
        self.generate_btn.config(state="disabled", text=self.loc.get_string('generating_btn'))
        self.cancel_btn.config(state="normal", text=self.loc.get_string('cancel_btn'))
        self.save_output_btn.config(state="disabled")
        self.controller.toggle_lang_buttons(enabled=False) # Disable lang switching

        self.last_auto_save_path = None
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')

        self.queue = queue.Queue()
        # --- MODIFIED: Pass the cancel_event to the worker thread ---
        self.generation_thread = threading.Thread(
            target=self.run_generation_worker,
            args=(self.cancel_event,),  # Pass the event as an argument
            daemon=True
        )
        self.generation_thread.start()
        self.after(100, self.check_queue)

    def cancel_generation(self):
        print(self.loc.get_string('gen_cancelled_log').strip())
        self.cancel_event.set()
        self.cancel_btn.config(state="disabled", text=self.loc.get_string('cancelling_btn'))

    def check_queue(self):
        try:
            result = self.queue.get(block=False)
            if isinstance(result, tuple) and len(result) == 3:
                _, result_text, auto_save_path = result
                is_error = "--- AN ERROR OCCURRED ---" in result_text
                if not is_error:
                    print(self.loc.get_string('gen_complete_log'))
                    self.last_auto_save_path = auto_save_path
                    self.save_output_btn.config(state="normal")
                # print(result_text) # This is already handled by StdoutRedirector now
            elif isinstance(result, str) and result == "CANCELLED":
                 # Message already printed in cancel_generation
                 pass
            # else:
            #     print(result) # Already handled

            # --- Reset UI state ---
            self.generate_btn.config(state="normal", text=self.loc.get_string('generate_btn'))
            self.cancel_btn.config(state="disabled", text=self.loc.get_string('cancel_btn'))
            self.controller.toggle_lang_buttons(enabled=True) # Re-enable lang switching
        except queue.Empty:
            self.after(100, self.check_queue)

    def run_generation_worker(self, cancel_event):
        try:
            config_obj = self.controller.config
            # ... set min/max credit
            min_credit_str = self.gen_vars["min_credit"].get().strip()
            max_credit_str = self.gen_vars["max_credit"].get().strip()
            limit_str = self.out_vars["limit"].get().strip()
            config_obj.generation_params["min_credit"] = int(min_credit_str) if min_credit_str else 30
            config_obj.generation_params["max_credit"] = int(max_credit_str) if max_credit_str else 42
            # ... set display params
            config_obj.display_params["limit_results"] = int(limit_str) if limit_str else None
            config_obj.display_params["sort_reverse"] = self.out_vars["sort_reverse"].get()

            # ... set filters
            def parse_cs_string(s): return [item.strip() for item in s.split(',')] if s.strip() else None

            config_obj.display_params["filters"]["day_num_condition"] = self.filter_vars["day_num_cond"].get()

            # Pass the state of the day checkboxes
            # We convert the IntVars to a simple dictionary for portability
            day_states = {day: var.get() for day, var in self.day_checkbox_vars.items()}
            config_obj.display_params["filters"]["day_specific_conditions"] = day_states

            # Pass the other course filters
            config_obj.display_params["filters"]["exclude_courses"] = parse_cs_string(self.filter_vars["exclude"].get())
            config_obj.display_params["filters"]["include_courses"] = parse_cs_string(self.filter_vars["include"].get())
            config_obj.display_params["filters"]["must_courses"] = parse_cs_string(self.filter_vars["must"].get())
            config_obj.display_params["sort_key"] = self.out_vars["sort_str"].get()
            config_obj.input["cache"]["enabled"] = self.gen_vars["load_if_possible"].get()
            self.controller.config.requirements = self.controller.requirements
            config_obj.update()
            cache_filepath = self._generate_cache_filename()
            config_obj.input["cache"]["filepath"] = cache_filepath
            print(self.loc.get_string('gen_config_updated_log'))
            summarized_programs, results_output, auto_save_path = run_program_generation(config_obj, cancel_event)

            if cancel_event.is_set():
                self.queue.put("CANCELLED")
            else:
                self.queue.put((summarized_programs, results_output, auto_save_path))

        except ValueError:
            self.queue.put((None, self.loc.get_string('gen_value_error_log'), None))
        except Exception as e:
            self.queue.put((None, self.loc.get_string('gen_error_log', e=e), None))

    def _on_day_checkbox_click(self, event, var):
        """
        Handles a click event on a day checkbox, manually cycling its
        variable and visual state. Returns 'break' to prevent default behavior.
        """
        checkbox_widget = event.widget

        # --- FIX: We now get the value directly from the passed IntVar ---
        current_state = var.get()
        next_state = (current_state + 1) % 3
        var.set(next_state)

        # Manually set the visual state of the widget
        if next_state == 0:  # Empty state
            checkbox_widget.state(['!selected', '!alternate'])
        elif next_state == 1:  # Checked state (✔)
            checkbox_widget.state(['selected', '!alternate'])
        elif next_state == 2:  # Crossed state (✘)
            checkbox_widget.state(['selected', 'alternate'])

        return "break"
