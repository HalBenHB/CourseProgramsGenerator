# src/gui.py (Corrected)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import sys
import threading
import queue
import shutil
import pandas as pd
import hashlib

from src import data_manager
from src.config import Config
from src.main import run_program_generation

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left', bg="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
    def hide_tip(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.configure(state='disabled')
    def write(self, string):
        self.text_widget.configure(state='normal')
        if string.startswith('\r'):
            self.text_widget.delete("end-1c linestart", "end")
            self.text_widget.insert("end", string.strip('\r'))
        else:
            self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
    def flush(self):
        self.text_widget.update_idletasks()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Course Program Generator")
        self.geometry("950x700")
        self.config = Config()
        self.config.update() # Initial update to build paths
        self.all_courses_list = {}
        self.requirements = []
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        self.frames = {}
        for F in (Screen1, Screen2, Screen3):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(Screen1)
    def show_frame(self, page_name): self.frames[page_name].tkraise()
    def get_frame(self, page_name): return self.frames[page_name]

class Screen1(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Welcome!", font=("Helvetica", 16)).pack(pady=20)
        ttk.Label(self, text="Select the offered courses file (e.g., course_offered_2425F.xls).").pack(pady=10)
        file_frame = ttk.Frame(self)
        file_frame.pack(pady=10, fill='x', padx=20)
        self.courses_filepath_var = tk.StringVar(value=self.controller.config.COURSES_FILEPATH)
        ttk.Entry(file_frame, textvariable=self.courses_filepath_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side="left", padx=5)
        ttk.Button(self, text="Load Courses and Continue", command=self.load_courses).pack(pady=20)
    def browse_file(self):
        initial_dir = os.path.dirname(self.controller.config.COURSES_FILEPATH or ".")
        filename = filedialog.askopenfilename(initialdir=initial_dir, title="Select Courses File", filetypes=(("Excel Files", "*.xls*"), ("All files", "*.*")))
        if filename: self.courses_filepath_var.set(filename)
    def load_courses(self):
        filepath = self.courses_filepath_var.get()
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File not found! Please check the path.")
            return
        try:
            config_obj = self.controller.config
            config_obj.courses_parameter = os.path.basename(filepath)
            config_obj.update()
            all_courses = data_manager.course_parses(config_obj)
            self.controller.all_courses_list = all_courses
            self.controller.get_frame(Screen2).update_course_list(list(all_courses.keys()))
            self.controller.show_frame(Screen2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or parse courses file:\n{e}")

class Screen2(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.currently_editing_req_index = None
        self.PREDEFINED_REQS = {
    "BABUS Özelleşilen Alan Seçmeli": {
        "file": "BABUS Özelleşilen Alan Seçmeli.xls",
        "needed": "<=3"
    },
    "BABUS Serbest Seçmeli": {
        "file": "BABUS Serbest Seçmeli.xls",
        "needed": "<=4"
    },
    "BABUS Program İçin Seçmeli (FIN)": {
        "file": "BABUS Program İçin Seçmeli (FIN).xls",
        "needed": "<=1"
    },
    "BABUS Program İçin Seçmeli (MGMT)": {
        "file": "BABUS Program İçin Seçmeli (MGMT).xls",
        "needed": "<=1"
    },
    "BABUS Program İçin Seçmeli (MIS)": {
        "file": "BABUS Program İçin Seçmeli (MIS).xls",
        "needed": "<=1"
    },
    "BABUS Program İçin Seçmeli (MKTG)": {
        "file": "BABUS Program İçin Seçmeli (MKTG).xls",
        "needed": "<=1"
    },
    "BABUS Program İçin Seçmeli (OPER)": {
        "file": "BABUS Program İçin Seçmeli (OPER).xls",
        "needed": "<=1"
    },
    "BSCS Program İçi Seçmeli": {
        "file": "BSCS Program İçi Seçmeli.xls",
        "needed": "<=3"
    },
    "BSCS FE Sosyal Bilimler Seçmeli": {
        "file": "BSCS FE Sosyal Bilimler Seçmeli.xls",
        "needed": "<=1"
    },
    "BSCS FE Sertifika Seçmeli": {
        "file": "BSCS FE Sertifika Seçmeli.xls",
        "needed": "<=2"
    },
    "BSCS FE Serbest Seçmeli": {
        "file": "BSCS FE Serbest Seçmeli.xls",
        "needed": "<=3"
    }
}
        ttk.Label(self, text="Requirement Builder", font=("Helvetica", 16)).pack(pady=10, fill="x")
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill="both", expand=True)
        courses_frame = ttk.LabelFrame(main_pane, text="Available Courses (Double-click to add)")
        main_pane.add(courses_frame, width=250)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_courses())
        ttk.Entry(courses_frame, textvariable=self.search_var).pack(fill="x", padx=5, pady=5)
        self.course_listbox = tk.Listbox(courses_frame, selectmode="extended", exportselection=False)
        self.course_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.course_listbox.bind('<Double-1>', self.add_course_to_requirement)
        editor_frame = ttk.LabelFrame(main_pane, text="Edit Selected Requirement")
        main_pane.add(editor_frame, width=350)
        ttk.Label(editor_frame, text="Requirement Name:").pack(fill="x", padx=5, pady=(5,0))
        self.editor_name_var = tk.StringVar()
        self.editor_name_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_name_entry = ttk.Entry(editor_frame, textvariable=self.editor_name_var)
        self.editor_name_entry.pack(fill="x", padx=5, pady=2)
        needed_frame = ttk.Frame(editor_frame)
        needed_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(needed_frame, text="Needed:").pack(side="left")
        self.editor_needed_op_var = tk.StringVar()
        self.editor_needed_op_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_needed_op_combo = ttk.Combobox(needed_frame, textvariable=self.editor_needed_op_var, values=["=", ">=", "<=", ">", "<"], width=4, state="readonly")
        self.editor_needed_op_combo.pack(side="left", padx=5)
        self.editor_needed_num_var = tk.StringVar()
        self.editor_needed_num_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_needed_num_entry = ttk.Entry(needed_frame, textvariable=self.editor_needed_num_var, width=5)
        self.editor_needed_num_entry.pack(side="left")
        add_remove_frame = ttk.Frame(editor_frame)
        add_remove_frame.pack(pady=5, fill="x")
        ttk.Button(add_remove_frame, text="-> Add Selected", command=self.add_course_to_requirement).pack(pady=2, padx=20)
        ttk.Button(add_remove_frame, text="<- Remove Selected", command=self.remove_course_from_requirement).pack(pady=2, padx=20)
        ttk.Label(editor_frame, text="Candidate Courses:").pack(fill="x", padx=5)
        self.editor_candidates_listbox = tk.Listbox(editor_frame, selectmode="extended", exportselection=False)
        self.editor_candidates_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        req_list_frame = ttk.LabelFrame(main_pane, text="Program Requirements")
        main_pane.add(req_list_frame, width=300)
        self.req_listbox = tk.Listbox(req_list_frame, exportselection=False)
        self.req_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.req_listbox.bind('<<ListboxSelect>>', self.on_req_select)
        req_btn_frame = ttk.Frame(req_list_frame)
        req_btn_frame.pack(fill="x", pady=5)
        ttk.Button(req_btn_frame, text="New Blank Requirement", command=self.create_new_requirement).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(req_btn_frame, text="Delete Selected", command=self.delete_selected_requirement).pack(side="left", expand=True, fill="x", padx=5)
        adder_frame = ttk.LabelFrame(req_list_frame, text="Quick Add Requirement")
        adder_frame.pack(fill="x", padx=5, pady=10)
        adder_options = list(self.PREDEFINED_REQS.keys()) + ["Add from Custom File..."]
        self.adder_combo = ttk.Combobox(adder_frame, values=adder_options, state="readonly")
        self.adder_combo.pack(fill="x", padx=5, pady=5)
        self.adder_combo.set("Select a template to add...")
        ttk.Button(adder_frame, text="Add", command=self.add_requirement_from_template).pack(pady=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10, side="bottom")
        ttk.Button(bottom_frame, text="Back", command=lambda: controller.show_frame(Screen1)).pack(side="left")
        ttk.Button(bottom_frame, text="Continue to Final Configuration", command=self.continue_to_screen3).pack(side="right")
        ttk.Button(bottom_frame, text="Save to JSON", command=self.save_reqs).pack(side="right", padx=10)
        ttk.Button(bottom_frame, text="Load Last Session", command=self.load_last_session).pack(side="right", padx=10)
        ttk.Button(bottom_frame, text="Load from JSON", command=lambda: self.load_reqs()).pack(side="right")
        self.update_editor_panel_state()
    def add_requirement_from_template(self):
        selection = self.adder_combo.get()
        if not selection or selection == "Select a template to add...":
            messagebox.showinfo("Info", "Please select a template from the dropdown first.")
            return
        if selection == "Add from Custom File...":
            filepath = filedialog.askopenfilename(title="Select Custom Course List File", filetypes=(("Excel Files", "*.xls*"), ("All Files", "*.*")))
            if not filepath: return
            req_name = os.path.splitext(os.path.basename(filepath))[0]
            needed = "=1"
            self._create_req_from_file(filepath, req_name, needed)
        else:
            req_config = self.PREDEFINED_REQS[selection]
            filepath = os.path.join(self.controller.config.INPUT_FILEPATH, req_config['file'])
            req_name = selection
            needed = req_config['needed']
            self._create_req_from_file(filepath, req_name, needed)
        self.adder_combo.set("Select a template to add...")
    def _create_req_from_file(self, filepath, req_name, needed_cond):
        try:
            df = pd.read_excel(filepath)
            if 'Ders' not in df.columns:
                messagebox.showerror("Format Error", "The selected Excel file must contain a column named 'Ders'.")
                return
            base_codes = df['Ders'].dropna().astype(str).tolist()
            expanded_candidates = []
            all_offered_courses = self.controller.all_courses_list.keys()
            for base_code in base_codes:
                found_match = False
                for full_code in all_offered_courses:
                    if full_code.startswith(base_code + '.'):
                        expanded_candidates.append(full_code)
                        found_match = True
                if not found_match: print(f"Info: Base course '{base_code}' from the list had no offered sections.")
            if not expanded_candidates: messagebox.showwarning("Warning", f"No offered courses found for the codes in '{os.path.basename(filepath)}'. An empty requirement was created.")
            new_req = {'name': req_name, 'needed': needed_cond, 'candidates': sorted(list(set(expanded_candidates)))}
            self.controller.requirements.append(new_req)
            self.update_req_listbox()
            self.req_listbox.selection_clear(0, tk.END)
            self.req_listbox.selection_set(tk.END)
            self.req_listbox.see(tk.END)
            self.on_req_select()
        except FileNotFoundError: messagebox.showerror("File Not Found", f"The required file was not found:\n{filepath}")
        except Exception as e: messagebox.showerror("Error", f"An unexpected error occurred while processing the file:\n{e}")
    def on_req_select(self, event=None):
        selected_indices = self.req_listbox.curselection()
        self.currently_editing_req_index = selected_indices[0] if selected_indices else None
        self.populate_editor_panel()
    def populate_editor_panel(self):
        if self.currently_editing_req_index is None:
            self.clear_editor_panel()
            self.update_editor_panel_state()
            return
        self.update_editor_panel_state()
        req = self.controller.requirements[self.currently_editing_req_index]
        for var in [self.editor_name_var, self.editor_needed_op_var, self.editor_needed_num_var]:
            traces = var.trace_info()
            if traces: var.trace_vdelete('w', traces[0][1])
        self.editor_name_var.set(req.get('name', ''))
        needed_str = req.get('needed', '=1')
        op = ''.join(filter(lambda x: not x.isdigit(), needed_str))
        num = ''.join(filter(str.isdigit, needed_str))
        self.editor_needed_op_var.set(op if op in self.editor_needed_op_combo['values'] else '=')
        self.editor_needed_num_var.set(num)
        self.editor_candidates_listbox.delete(0, tk.END)
        for candidate in sorted(req.get('candidates', [])): self.editor_candidates_listbox.insert(tk.END, candidate)
        for var, trace_func in [(self.editor_name_var, self.update_requirement_from_editor), (self.editor_needed_op_var, self.update_requirement_from_editor), (self.editor_needed_num_var, self.update_requirement_from_editor)]:
            var.trace_add("write", trace_func)
    def clear_editor_panel(self):
        self.editor_name_var.set("")
        self.editor_needed_op_var.set("=")
        self.editor_needed_num_var.set("1")
        self.editor_candidates_listbox.delete(0, tk.END)
    def update_editor_panel_state(self):
        state = "normal" if self.currently_editing_req_index is not None else "disabled"
        for widget in [self.editor_name_entry, self.editor_needed_op_combo, self.editor_needed_num_entry, self.editor_candidates_listbox]:
            widget.config(state=state)
    def update_req_listbox(self):
        self.req_listbox.delete(0, tk.END)
        for req in self.controller.requirements:
            display_text = f"REQ: {req.get('name', 'N/A')} | Needed: {req.get('needed', 'N/A')} | Candidates: {len(req.get('candidates', []))}"
            self.req_listbox.insert(tk.END, display_text)
    def update_requirement_from_editor(self, *args):
        if self.currently_editing_req_index is None: return
        req = self.controller.requirements[self.currently_editing_req_index]
        req['name'] = self.editor_name_var.get()
        req['needed'] = f"{self.editor_needed_op_var.get()}{self.editor_needed_num_var.get()}"
        display_text = f"REQ: {req['name']} | Needed: {req['needed']} | Candidates: {len(req.get('candidates', []))}"
        self.req_listbox.delete(self.currently_editing_req_index)
        self.req_listbox.insert(self.currently_editing_req_index, display_text)
        self.req_listbox.selection_set(self.currently_editing_req_index)
    def create_new_requirement(self):
        new_req = {"name": f"New Requirement {len(self.controller.requirements) + 1}", "needed": "=1", "candidates": []}
        self.controller.requirements.append(new_req)
        self.update_req_listbox()
        self.req_listbox.selection_clear(0, tk.END)
        self.req_listbox.selection_set(tk.END)
        self.req_listbox.see(tk.END)
        self.on_req_select()
    def delete_selected_requirement(self):
        if self.currently_editing_req_index is None:
            messagebox.showwarning("Warning", "Please select a requirement to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this requirement?"):
            self.controller.requirements.pop(self.currently_editing_req_index)
            self.currently_editing_req_index = None
            self.update_req_listbox()
            self.clear_editor_panel()
            self.update_editor_panel_state()
    def add_course_to_requirement(self, event=None):
        if self.currently_editing_req_index is None:
            messagebox.showwarning("Action Required", "Please create or select a requirement first.")
            return
        selected_indices = self.course_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select one or more courses from 'Available Courses'.")
            return
        req = self.controller.requirements[self.currently_editing_req_index]
        current_candidates = set(req.get('candidates', []))
        for i in selected_indices:
            course = self.course_listbox.get(i)
            if course not in current_candidates: req.setdefault('candidates', []).append(course)
        self.populate_editor_panel()
        self.update_requirement_from_editor()
    def remove_course_from_requirement(self):
        if self.currently_editing_req_index is None: return
        selected_indices = self.editor_candidates_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select courses from 'Candidate Courses' to remove.")
            return
        req = self.controller.requirements[self.currently_editing_req_index]
        courses_to_remove = {self.editor_candidates_listbox.get(i) for i in selected_indices}
        req['candidates'] = [c for c in req.get('candidates', []) if c not in courses_to_remove]
        self.populate_editor_panel()
        self.update_requirement_from_editor()
    def update_course_list(self, course_names):
        self.course_listbox.delete(0, tk.END)
        for course in sorted(course_names): self.course_listbox.insert(tk.END, course)
    def filter_courses(self):
        search_term = self.search_var.get().lower()
        self.course_listbox.delete(0, tk.END)
        all_course_names = self.controller.all_courses_list.keys()
        for course in all_course_names:
            if search_term in course.lower(): self.course_listbox.insert(tk.END, course)
    def save_reqs(self):
        if not self.controller.requirements: return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, 'w') as f: json.dump(self.controller.requirements, f, indent=4)
            messagebox.showinfo("Success", f"Requirements saved to {os.path.basename(path)}")
    def load_reqs(self, path=None):
        if not path:
            path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path and os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    loaded_reqs = json.load(f)
                for req in loaded_reqs:
                    if 'requirement_name' in req and 'name' not in req:
                        req['name'] = req.pop('requirement_name')
                self.controller.requirements = loaded_reqs
                self.currently_editing_req_index = None
                self.clear_editor_panel()
                self.update_editor_panel_state()
                self.update_req_listbox()
                if self.controller.requirements:
                    self.req_listbox.selection_set(0)
                    self.on_req_select()
                messagebox.showinfo("Success", f"Loaded {len(self.controller.requirements)} requirements.")
            except Exception as e: messagebox.showerror("Error", f"Failed to load or parse JSON file:\n{e}")
    def load_last_session(self):
        temp_req_path = os.path.join(self.controller.config.INPUT_FILEPATH, "requirements_gui_temp.json")
        if not os.path.exists(temp_req_path):
            messagebox.showinfo("Info", "No last session file found to load.")
            return
        self.load_reqs(path=temp_req_path)
    def continue_to_screen3(self):
        if not self.controller.requirements:
            messagebox.showerror("Error", "You must create or load at least one requirement.")
            return
        # Use the requirements from the controller's memory, which is the single source of truth
        self.controller.config.requirements = self.controller.requirements
        temp_req_path = os.path.join(self.controller.config.INPUT_FILEPATH, "requirements_gui_temp.json")
        with open(temp_req_path, 'w') as f: json.dump(self.controller.requirements, f)
        self.controller.config.requirements_parameter = os.path.basename(temp_req_path)
        self.controller.show_frame(Screen3)

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
            "sort": "How to sort the final list. Use Python dictionary syntax.\nExample: program['total_days']",
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
            "min_credit": tk.StringVar(value=self.controller.config.min_credit),
            "max_credit": tk.StringVar(value=self.controller.config.max_credit),
            "load_if_possible": tk.BooleanVar(value=True)
        }
        ttk.Label(gen_frame, text="Min/Max Credits:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(gen_frame, textvariable=self.gen_vars["min_credit"], width=5).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(gen_frame, textvariable=self.gen_vars["max_credit"], width=5).grid(row=0, column=2, sticky="w", pady=2)
        Tooltip(ttk.Label(gen_frame, text="(?)", cursor="question_arrow"), help_texts["credits"]).widget.grid(row=0, column=3, sticky="w", padx=5)
        cache_check = ttk.Checkbutton(gen_frame, text="Load cached programs if available", variable=self.gen_vars["load_if_possible"])
        cache_check.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        Tooltip(cache_check, help_texts["cache"])
        out_frame = ttk.LabelFrame(top_frame, text="Output Parameters")
        out_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.out_vars = {"limit": tk.StringVar(value=self.controller.config.limit_number_of_programs), "sort_str": tk.StringVar(value=self.controller.config.sort_condition_str), "sort_reverse": tk.BooleanVar(value=False)}
        ttk.Label(out_frame, text="Limit Programs:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(out_frame, textvariable=self.out_vars["limit"], width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        Tooltip(ttk.Label(out_frame, text="(?)", cursor="question_arrow"), help_texts["limit"]).widget.grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(out_frame, text="Sort By:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(out_frame, textvariable=self.out_vars["sort_str"], width=20).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(out_frame, text="Descending", variable=self.out_vars["sort_reverse"]).grid(row=1, column=2, sticky="w")
        Tooltip(ttk.Label(out_frame, text="(?)", cursor="question_arrow"), help_texts["sort"]).widget.grid(row=1, column=3, sticky="w", padx=5)
        filter_frame = ttk.LabelFrame(self, text="Filtering")
        filter_frame.pack(fill="x", padx=5, pady=5)
        filter_frame.columnconfigure(1, weight=1)
        self.filter_vars = {"day_cond": tk.StringVar(), "exclude": tk.StringVar(), "include": tk.StringVar(), "must": tk.StringVar()}
        row_map = [("Day Conditions:", "day_cond"), ("Exclude Courses:", "exclude"), ("Include At Least One:", "include"), ("Must Have Courses:", "must")]
        for i, (label_text, key) in enumerate(row_map):
            ttk.Label(filter_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Entry(filter_frame, textvariable=self.filter_vars[key], width=40).grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            Tooltip(ttk.Label(filter_frame, text="(?)", cursor="question_arrow"), help_texts[key]).widget.grid(row=i, column=2, sticky="w", padx=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10)
        ttk.Button(bottom_frame, text="Back", command=lambda: controller.show_frame(Screen2)).pack(side="left")
        self.generate_btn = ttk.Button(bottom_frame, text="GENERATE PROGRAMS", command=self.start_generation_thread)
        self.generate_btn.pack(side="right")
        self.save_output_btn = ttk.Button(bottom_frame, text="Save Output As...", command=self.save_output, state="disabled")
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
        courses_basename = os.path.splitext(config_obj.courses_parameter)[0]
        req_string = json.dumps(self.controller.requirements, sort_keys=True, separators=(',', ':'))
        req_hash = hashlib.sha256(req_string.encode('utf-8')).hexdigest()[:16]
        safe_courses_name = "".join(c for c in courses_basename if c.isalnum() or c in (' ', '_')).rstrip()
        cache_filename = f"cache_{safe_courses_name}_reqs_{req_hash}_cr_{config_obj.min_credit}-{config_obj.max_credit}.pkl"
        if not config_obj.INPUT_FILEPATH: config_obj.update()
        return os.path.join(config_obj.INPUT_FILEPATH, cache_filename)
    def save_output(self):
        if not self.last_auto_save_path or not os.path.exists(self.last_auto_save_path):
            messagebox.showwarning("Warning", "No auto-saved output file found. Please generate programs first.")
            return
        default_filename = os.path.basename(self.last_auto_save_path)
        destination_path = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".txt", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")), title="Save Output As")
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
            min_credit_str = self.gen_vars["min_credit"].get().strip()
            max_credit_str = self.gen_vars["max_credit"].get().strip()
            limit_str = self.out_vars["limit"].get().strip()
            config_obj.min_credit = int(min_credit_str) if min_credit_str else 30
            config_obj.max_credit = int(max_credit_str) if max_credit_str else 42
            config_obj.limit_number_of_programs = int(limit_str) if limit_str else None
            config_obj.sort_reverse = self.out_vars["sort_reverse"].get()
            def parse_cs_string(s): return [item.strip() for item in s.split(',')] if s.strip() else None
            config_obj.day_conditions = parse_cs_string(self.filter_vars["day_cond"].get())
            config_obj.exclude_courses = parse_cs_string(self.filter_vars["exclude"].get())
            config_obj.include_courses = parse_cs_string(self.filter_vars["include"].get())
            config_obj.must_courses = parse_cs_string(self.filter_vars["must"].get())
            config_obj.sort_condition_str = self.out_vars["sort_str"].get()
            config_obj.load_programs_if_saved = self.gen_vars["load_if_possible"].get()
            self.controller.config.requirements = self.controller.requirements
            config_obj.update()
            cache_filepath = self._generate_cache_filename()
            config_obj.generation["programs_file_path"] = cache_filepath
            print("Configuration updated. Starting generation process...\n")
            summarized_programs, results_output, auto_save_path = run_program_generation(config_obj)
            self.queue.put((summarized_programs, results_output, auto_save_path))
        except ValueError:
            self.queue.put(("\n--- AN ERROR OCCURRED ---\nError: Please ensure Min/Max Credits and Limit Programs are valid numbers.",))
        except Exception as e:
            self.queue.put((f"\n--- AN ERROR OCCURRED ---\n{e}",))

if __name__ == "__main__":
    app = App()
    app.mainloop()