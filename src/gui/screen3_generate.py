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
        self.generation_thread = None
        self.last_auto_save_path = None
        ttk.Label(self, text="Final Configuration & Generation", font=("Helvetica", 16)).pack(pady=10)
        help_texts = {
            "credits": "Set the desired range for total ECTS credits in a program.\nLeave empty to use defaults (30-42).",
            "limit": "The maximum number of valid programs to display.\nLeave empty for NO LIMIT.",
            "sort": "How to sort the final list. Use Python dictionary syntax.\nExample: total_days, total_credits, total_hours, __len__",
            "cache": "If checked, the app will load pre-calculated programs if the\ncourse list, requirements, and credit limits haven't changed,\nsaving significant time. Uncheck to force a new calculation.",
            "day_cond": "Filter by the number of days with classes. Comma-separated.\nExample: <5",
            "exclude": "Programs with ANY of these courses will be removed. Comma-separated.\nExample: CS 447.A, ACC 201.A",
            "include": "Programs must have AT LEAST ONE of these. Comma-separated.\nExample: BUS 302.A, ECO 410.A",
            "must": "Programs MUST have ALL of these courses. Comma-separated.\nExample: CS 333.A, HIST 101.A"
        }
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", expand=True)
        gen_frame = ttk.LabelFrame(top_frame, text="Generation Parameters")
        gen_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.gen_vars = {
            "min_credit": tk.StringVar(value=self.controller.config.generation_params["min_credit"]),
            "max_credit": tk.StringVar(value=self.controller.config.generation_params["max_credit"]),
            "load_if_possible": tk.BooleanVar(value=self.controller.config.input["cache"]["enabled"])
        }

        ttk.Label(gen_frame, text="Min/Max Credits:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(gen_frame, textvariable=self.gen_vars["min_credit"], width=5).grid(row=0, column=1, sticky="w",
                                                                                     padx=5, pady=2)
        ttk.Entry(gen_frame, textvariable=self.gen_vars["max_credit"], width=5).grid(row=0, column=2, sticky="w",
                                                                                     pady=2)
        Tooltip(ttk.Label(gen_frame, text="(?)", cursor="question_arrow"), help_texts["credits"]).widget.grid(row=0,
                                                                                                              column=3,
                                                                                                              sticky="w",
                                                                                                              padx=5)
        cache_check = ttk.Checkbutton(gen_frame, text="Load cached programs if available",
                                      variable=self.gen_vars["load_if_possible"])
        cache_check.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        Tooltip(cache_check, help_texts["cache"])
        out_frame = ttk.LabelFrame(top_frame, text="Output Parameters")
        out_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.out_vars = {
            "limit": tk.StringVar(value=self.controller.config.display_params["limit_results"]),
            "sort_str": tk.StringVar(value=self.controller.config.display_params["sort_key"]),
            "sort_reverse": tk.BooleanVar(value=self.controller.config.display_params["sort_reverse"])
        }
        ttk.Label(out_frame, text="Limit Programs:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(out_frame, textvariable=self.out_vars["limit"], width=10).grid(row=0, column=1, sticky="w", padx=5,
                                                                                 pady=2)
        Tooltip(ttk.Label(out_frame, text="(?)", cursor="question_arrow"), help_texts["limit"]).widget.grid(row=0,
                                                                                                            column=2,
                                                                                                            sticky="w",
                                                                                                            padx=5)
        ttk.Label(out_frame, text="Sort By:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(out_frame, textvariable=self.out_vars["sort_str"], width=20).grid(row=1, column=1, sticky="w", padx=5,
                                                                                    pady=2)
        ttk.Checkbutton(out_frame, text="Descending", variable=self.out_vars["sort_reverse"]).grid(row=1, column=2,
                                                                                                   sticky="w")
        Tooltip(ttk.Label(out_frame, text="(?)", cursor="question_arrow"), help_texts["sort"]).widget.grid(row=1,
                                                                                                           column=3,
                                                                                                           sticky="w",
                                                                                                           padx=5)
        filter_frame = ttk.LabelFrame(self, text="Filtering")
        filter_frame.pack(fill="x", padx=5, pady=5)
        filter_frame.columnconfigure(1, weight=1)
        self.filter_vars = {"day_cond": tk.StringVar(), "exclude": tk.StringVar(), "include": tk.StringVar(),
                            "must": tk.StringVar()}
        row_map = [("Day Conditions:", "day_cond"), ("Exclude Courses:", "exclude"),
                   ("Include At Least One:", "include"), ("Must Have Courses:", "must")]
        for i, (label_text, key) in enumerate(row_map):
            ttk.Label(filter_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Entry(filter_frame, textvariable=self.filter_vars[key], width=40).grid(row=i, column=1, sticky="ew",
                                                                                       padx=5, pady=2)
            Tooltip(ttk.Label(filter_frame, text="(?)", cursor="question_arrow"), help_texts[key]).widget.grid(row=i,
                                                                                                               column=2,
                                                                                                               sticky="w",
                                                                                                               padx=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10)
        ttk.Button(bottom_frame, text="Back", command=lambda: controller.show_screen2()).pack(side="left")
        self.generate_btn = ttk.Button(bottom_frame, text="GENERATE PROGRAMS", command=self.start_generation_thread)
        self.generate_btn.pack(side="right")
        self.save_output_btn = ttk.Button(bottom_frame, text="Save Output As...", command=self.save_output,
                                          state="disabled")
        self.save_output_btn.pack(side="right", padx=10)
        log_frame = ttk.LabelFrame(self, text="Output Log")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_text = tk.Text(log_frame, wrap="word", height=15)
        self.output_text.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.pack(fill="y", side="right")
        self.output_text.config(yscrollcommand=scrollbar.set)
        sys.stdout = StdoutRedirector(self.output_text)

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
            messagebox.showwarning("Warning", "No auto-saved output file found. Please generate programs first.")
            return
        default_filename = os.path.basename(self.last_auto_save_path)
        destination_path = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".txt",
                                                        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")),
                                                        title="Save Output As")
        if destination_path:
            try:
                shutil.copy(self.last_auto_save_path, destination_path)
                messagebox.showinfo("Success", f"Output file copied to:\n{destination_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy file: {e}")

    def start_generation_thread(self):
        self.generate_btn.config(state="disabled", text="Generating...")
        self.save_output_btn.config(state="disabled")
        self.last_auto_save_path = None
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        self.queue = queue.Queue()
        self.generation_thread = threading.Thread(target=self.run_generation_worker, daemon=True)
        self.generation_thread.start()
        self.after(100, self.check_queue)

    def check_queue(self):
        try:
            result = self.queue.get(block=False)
            if isinstance(result, tuple) and len(result) == 3:
                summarized_programs, result_text, auto_save_path = result
                is_error = "--- AN ERROR OCCURRED ---" in result_text
                if not is_error:
                    print("\n--- GENERATION COMPLETE ---")
                    self.last_auto_save_path = auto_save_path
                    self.save_output_btn.config(state="normal")
                print(result_text)
            else:
                print(result)
            self.generate_btn.config(state="normal", text="GENERATE PROGRAMS")
        except queue.Empty:
            self.after(100, self.check_queue)

    def run_generation_worker(self):
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
            def parse_cs_string(s):
                return [item.strip() for item in s.split(',')] if s.strip() else None

            config_obj.display_params["filters"]["day_conditions"] = parse_cs_string(self.filter_vars["day_cond"].get())
            config_obj.display_params["filters"]["exclude_courses"] = parse_cs_string(self.filter_vars["exclude"].get())
            config_obj.display_params["filters"]["include_courses"] = parse_cs_string(self.filter_vars["include"].get())
            config_obj.display_params["filters"]["must_courses"] = parse_cs_string(self.filter_vars["must"].get())
            config_obj.display_params["sort_key"] = self.out_vars["sort_str"].get()
            config_obj.input["cache"]["enabled"] = self.gen_vars["load_if_possible"].get()
            self.controller.config.requirements = self.controller.requirements
            config_obj.update()
            cache_filepath = self._generate_cache_filename()
            config_obj.input["cache"]["filepath"] = cache_filepath
            print("Configuration updated. Starting generation process...\n")
            summarized_programs, results_output, auto_save_path = run_program_generation(config_obj)
            self.queue.put((summarized_programs, results_output, auto_save_path))
        except ValueError:
            self.queue.put(
                ("\n--- AN ERROR OCCURRED ---\nError: Please ensure Min/Max Credits and Limit Programs are valid numbers.",))
        except Exception as e:
            self.queue.put((f"\n--- AN ERROR OCCURRED ---\n{e}",))
