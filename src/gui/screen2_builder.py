import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd


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
            },
            "TLL 101 Offered Branches": {
                "file": "TLL101.xls",
                "needed": "=1"
            },
            "TLL 102 Offered Branches": {
                "file": "TLL102.xls",
                "needed": "=1"
            },
            "ENG 101 Offered Branches": {
                "file": "ENG101.xls",
                "needed": "=1"
            },
            "ENG 102 Offered Branches": {
                "file": "ENG102.xls",
                "needed": "=1"
            },
            "HIST 201 Offered Branches": {
                "file": "HIST201.xls",
                "needed": "=1"
            },
            "HIST 202 Offered Branches": {
                "file": "HIST202.xls",
                "needed": "=1"
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
        ttk.Label(editor_frame, text="Requirement Name:").pack(fill="x", padx=5, pady=(5, 0))
        self.editor_name_var = tk.StringVar()
        self.editor_name_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_name_entry = ttk.Entry(editor_frame, textvariable=self.editor_name_var)
        self.editor_name_entry.pack(fill="x", padx=5, pady=2)
        needed_frame = ttk.Frame(editor_frame)
        needed_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(needed_frame, text="Needed:").pack(side="left")
        self.editor_needed_op_var = tk.StringVar()
        self.editor_needed_op_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_needed_op_combo = ttk.Combobox(needed_frame, textvariable=self.editor_needed_op_var,
                                                   values=["=", ">=", "<=", ">", "<"], width=4, state="readonly")
        self.editor_needed_op_combo.pack(side="left", padx=5)
        self.editor_needed_num_var = tk.StringVar()
        self.editor_needed_num_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_needed_num_entry = ttk.Entry(needed_frame, textvariable=self.editor_needed_num_var, width=5)
        self.editor_needed_num_entry.pack(side="left")
        add_remove_frame = ttk.Frame(editor_frame)
        add_remove_frame.pack(pady=5, fill="x")
        ttk.Button(add_remove_frame, text="-> Add Selected", command=self.add_course_to_requirement).pack(pady=2,
                                                                                                          padx=20)
        ttk.Button(add_remove_frame, text="<- Remove Selected", command=self.remove_course_from_requirement).pack(
            pady=2, padx=20)
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
        ttk.Button(req_btn_frame, text="New Blank Requirement", command=self.create_new_requirement).pack(side="left",
                                                                                                          expand=True,
                                                                                                          fill="x",
                                                                                                          padx=5)
        ttk.Button(req_btn_frame, text="Delete Selected", command=self.delete_selected_requirement).pack(side="left",
                                                                                                         expand=True,
                                                                                                         fill="x",
                                                                                                         padx=5)
        adder_frame = ttk.LabelFrame(req_list_frame, text="Quick Add Requirement")
        adder_frame.pack(fill="x", padx=5, pady=10)
        adder_options = list(self.PREDEFINED_REQS.keys()) + ["Add from Custom File..."]
        self.adder_combo = ttk.Combobox(adder_frame, values=adder_options, state="readonly")
        self.adder_combo.pack(fill="x", padx=5, pady=5)
        self.adder_combo.set("Select a template to add...")
        ttk.Button(adder_frame, text="Add", command=self.add_requirement_from_template).pack(pady=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10, side="bottom")
        ttk.Button(bottom_frame, text="Back", command=lambda: controller.show_screen1()).pack(side="left")
        ttk.Button(bottom_frame, text="Continue to Final Configuration", command=self.continue_to_screen3).pack(
            side="right")
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
            filepath = filedialog.askopenfilename(title="Select Custom Course List File",
                                                  filetypes=(("Excel Files", "*.xls*"), ("All Files", "*.*")))
            if not filepath: return
            req_name = os.path.splitext(os.path.basename(filepath))[0]
            needed = "=1"
            self._create_req_from_file(filepath, req_name, needed)
        else:
            req_config = self.PREDEFINED_REQS[selection]
            filepath = os.path.join(self.controller.config.paths["pre_reqs_dir"], req_config['file'])
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
            if not expanded_candidates: messagebox.showwarning("Warning",
                                                               f"No offered courses found for the codes in '{os.path.basename(filepath)}'. An empty requirement was created.")
            new_req = {'name': req_name, 'needed': needed_cond, 'candidates': sorted(list(set(expanded_candidates)))}
            self.controller.requirements.append(new_req)
            self.update_req_listbox()
            self.req_listbox.selection_clear(0, tk.END)
            self.req_listbox.selection_set(tk.END)
            self.req_listbox.see(tk.END)
            self.on_req_select()
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"The required file was not found:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while processing the file:\n{e}")

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
        for var, trace_func in [(self.editor_name_var, self.update_requirement_from_editor),
                                (self.editor_needed_op_var, self.update_requirement_from_editor),
                                (self.editor_needed_num_var, self.update_requirement_from_editor)]:
            var.trace_add("write", trace_func)

    def clear_editor_panel(self):
        self.editor_name_var.set("")
        self.editor_needed_op_var.set("=")
        self.editor_needed_num_var.set("1")
        self.editor_candidates_listbox.delete(0, tk.END)

    def update_editor_panel_state(self):
        state = "normal" if self.currently_editing_req_index is not None else "disabled"
        for widget in [self.editor_name_entry, self.editor_needed_op_combo, self.editor_needed_num_entry,
                       self.editor_candidates_listbox]:
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
        path = filedialog.asksaveasfilename(
            initialdir=self.controller.config.paths["reqs_dir"],
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            with open(path, 'w') as f: json.dump(self.controller.requirements, f, indent=4)
            messagebox.showinfo("Success", f"Requirements saved to {os.path.basename(path)}")

    def load_reqs(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                initialdir=self.controller.config.paths["reqs_dir"],
                filetypes=[("JSON files", "*.json")]
            )
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
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load or parse JSON file:\n{e}")

    def load_last_session(self):
        temp_req_path = os.path.join(self.controller.config.paths["reqs_dir"], "requirements_gui_temp.json")
        if not os.path.exists(temp_req_path):
            messagebox.showinfo("Info", "No last session file found to load.")
            return
        self.load_reqs(path=temp_req_path)

    def continue_to_screen3(self):
        if not self.controller.requirements:
            messagebox.showerror("Error", "You must create or load at least one requirement.")
            return
        # Use the requirements from the controller's memory, which is the single source of truth
        self.controller.config.requirements = self.controller.requirements  # Keep this for now, it's the live edited data
        temp_req_path = os.path.join(self.controller.config.paths["reqs_dir"], "requirements_gui_temp.json")
        with open(temp_req_path, 'w') as f: json.dump(self.controller.requirements, f)
        self.controller.config.input["requirements"]["basename"] = os.path.basename(temp_req_path)
        self.controller.show_screen3()