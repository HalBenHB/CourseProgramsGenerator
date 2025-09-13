import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from src import data_manager

class Screen1(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.loc = controller.loc

        # --- Widget Creation (without text) ---
        self.welcome_label = ttk.Label(self, font=("Helvetica", 16))
        self.welcome_label.pack(pady=20)

        self.select_file_label = ttk.Label(self)
        self.select_file_label.pack(pady=10)

        file_frame = ttk.Frame(self)
        file_frame.pack(pady=10, fill='x', padx=20)

        self.courses_filepath_var = tk.StringVar(value=self.controller.config.input["courses"]["filepath"])
        ttk.Entry(file_frame, textvariable=self.courses_filepath_var, width=60).pack(side="left", fill="x", expand=True)

        self.browse_button = ttk.Button(file_frame, command=self.browse_file)
        self.browse_button.pack(side="left", padx=5)

        self.load_button = ttk.Button(self, command=self.load_courses)
        self.load_button.pack(pady=20)

        # --- NEW: Cache Management Section ---
        self.cache_frame = ttk.LabelFrame(self)
        self.cache_frame.pack(pady=20, padx=20, fill='x')

        self.clear_cache_var = tk.BooleanVar(value=True)
        self.clear_outputs_var = tk.BooleanVar(value=True)

        self.clear_cache_check = ttk.Checkbutton(self.cache_frame, variable=self.clear_cache_var)
        self.clear_cache_check.pack(anchor='w', padx=10)

        self.clear_outputs_check = ttk.Checkbutton(self.cache_frame, variable=self.clear_outputs_var)
        self.clear_outputs_check.pack(anchor='w', padx=10)

        self.clear_button = ttk.Button(self.cache_frame, command=self.clear_cache_files)
        self.clear_button.pack(pady=10)

        # Set initial text
        self.update_text()

    def update_text(self):
        """Update all text elements on this screen to the current language."""
        self.welcome_label.config(text=self.loc.get_string('screen1_welcome'))
        self.select_file_label.config(text=self.loc.get_string('screen1_select_file'))
        self.browse_button.config(text=self.loc.get_string('browse'))
        self.load_button.config(text=self.loc.get_string('load_and_continue'))

        # Update new cache management widgets
        self.cache_frame.config(text=self.loc.get_string('cache_mgmt_label'))
        self.clear_cache_check.config(text=self.loc.get_string('clear_program_cache_label'))
        self.clear_outputs_check.config(text=self.loc.get_string('clear_saved_outputs_label'))
        self.clear_button.config(text=self.loc.get_string('clear_cache_btn'))

    def clear_cache_files(self):
        """Deletes selected cache and output files after user confirmation."""
        clear_caches = self.clear_cache_var.get()
        clear_outputs = self.clear_outputs_var.get()

        if not clear_caches and not clear_outputs:
            messagebox.showinfo(self.loc.get_string('info'), self.loc.get_string('nothing_to_clear_msg'))
            return

        # Confirm with the user before deleting files
        if not messagebox.askyesno(self.loc.get_string('confirm_clear_title'), self.loc.get_string('confirm_clear_msg')):
            return

        cleared_items = []

        # Clear Program Caches (.pkl)
        if clear_caches:
            cache_dir = self.controller.config.paths["cache_dir"]
            try:
                if os.path.exists(cache_dir):
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    cleared_items.append(self.loc.get_string('cleared_caches_item'))
            except Exception as e:
                messagebox.showerror(self.loc.get_string('error'), f"Could not clear program cache:\n{e}")

        # Clear Saved Outputs (.txt)
        if clear_outputs:
            output_dir = self.controller.config.paths["output_dir"]
            try:
                if os.path.exists(output_dir):
                    for filename in os.listdir(output_dir):
                        file_path = os.path.join(output_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    cleared_items.append(self.loc.get_string('cleared_outputs_item'))
            except Exception as e:
                messagebox.showerror(self.loc.get_string('error'), f"Could not clear saved outputs:\n{e}")

        # Report success
        if cleared_items:
            messagebox.showinfo("Success", self.loc.get_string('clear_success_msg', cleared_items='\n'.join(cleared_items)))

    def browse_file(self):
        initial_dir = os.path.dirname(self.controller.config.input["courses"]["filepath"] or ".")
        filename = filedialog.askopenfilename(initialdir=initial_dir, title="Select Courses File",
                                              filetypes=(("Excel Files", "*.xls*"), ("All files", "*.*")))
        if filename: self.courses_filepath_var.set(filename)

    def load_courses(self):
        filepath = self.courses_filepath_var.get()
        if not os.path.exists(filepath):
            messagebox.showerror(self.loc.get_string('error'), self.loc.get_string('file_not_found_msg'))
            return
        try:
            config_obj = self.controller.config
            config_obj.input["courses"]["basename"] = os.path.basename(filepath)
            config_obj.update()
            all_courses = data_manager.parse_courses_from_excel(config_obj.input["courses"]["filepath"])
            self.controller.all_courses_list = all_courses
            self.controller.on_courses_loaded()
        except Exception as e:
            messagebox.showerror(self.loc.get_string('error'), self.loc.get_string('file_load_error_msg', e=e))