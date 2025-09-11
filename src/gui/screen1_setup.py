import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from src import data_manager

class Screen1(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Welcome!", font=("Helvetica", 16)).pack(pady=20)
        ttk.Label(self, text="Select the offered courses file (e.g., course_offered_2425F.xls).").pack(pady=10)
        file_frame = ttk.Frame(self)
        file_frame.pack(pady=10, fill='x', padx=20)
        self.courses_filepath_var = tk.StringVar(value=self.controller.config.input["courses"]["filepath"])
        ttk.Entry(file_frame, textvariable=self.courses_filepath_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side="left", padx=5)
        ttk.Button(self, text="Load Courses and Continue", command=self.load_courses).pack(pady=20)

    def browse_file(self):
        initial_dir = os.path.dirname(self.controller.config.input["courses"]["filepath"] or ".")
        filename = filedialog.askopenfilename(initialdir=initial_dir, title="Select Courses File",
                                              filetypes=(("Excel Files", "*.xls*"), ("All files", "*.*")))
        if filename: self.courses_filepath_var.set(filename)

    def load_courses(self):
        filepath = self.courses_filepath_var.get()
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File not found! Please check the path.")
            return
        try:
            config_obj = self.controller.config
            config_obj.input["courses"]["basename"] = os.path.basename(filepath)  # Set the basename
            config_obj.update()  # update() will build the full path
            # Pass the full path to course_parses
            all_courses = data_manager.course_parses(config_obj.input["courses"]["filepath"])
            self.controller.all_courses_list = all_courses
            self.controller.on_courses_loaded()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or parse courses file:\n{e}")
