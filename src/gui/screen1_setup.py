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

        # Set initial text
        self.update_text()

    def update_text(self):
        """Update all text elements on this screen to the current language."""
        self.welcome_label.config(text=self.loc.get_string('screen1_welcome'))
        self.select_file_label.config(text=self.loc.get_string('screen1_select_file'))
        self.browse_button.config(text=self.loc.get_string('browse'))
        self.load_button.config(text=self.loc.get_string('load_and_continue'))

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