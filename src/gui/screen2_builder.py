# src/gui/screen2_builder.py

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from .predefined_reqs_data import PREDEFINED_REQS_KEYS

class Screen2(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.loc = controller.loc
        self.currently_editing_req_index = None
        self.double_click_locked = False

        # --- MODIFIED: Data is now imported, not defined here ---
        self.PREDEFINED_REQS_KEYS = PREDEFINED_REQS_KEYS



        # --- WIDGET CREATION (without text) ---
        self.title_label = ttk.Label(self, font=("Helvetica", 16))
        self.title_label.pack(pady=10, fill="x")

        # --- MODIFIED: Use builder methods for a cleaner __init__ ---
        main_pane = self._setup_panes()
        self._create_left_panel(main_pane)
        self._create_center_panel(main_pane)
        self._create_right_panel(main_pane)
        self._create_bottom_panel()

        self.update_text()
        self.update_editor_panel_state()

    # --- NEW: UI Builder Methods ---
    def _setup_panes(self):
        """Creates and packs the main PanedWindow."""
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill="both", expand=True)
        return main_pane

    def _create_left_panel(self, parent_pane):
        """Builds the 'Available Courses' panel."""
        self.courses_frame = ttk.LabelFrame(parent_pane)
        parent_pane.add(self.courses_frame, width=250)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_courses())
        ttk.Entry(self.courses_frame, textvariable=self.search_var).pack(fill="x", padx=5, pady=5)
        self.course_listbox = tk.Listbox(self.courses_frame, selectmode="extended", exportselection=False)
        self.course_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.course_listbox.bind('<Double-1>', self.add_course_to_requirement)

    def _create_center_panel(self, parent_pane):
        """Builds the 'Edit Selected Requirement' panel."""
        editor_frame = ttk.LabelFrame(parent_pane)
        parent_pane.add(editor_frame, width=350)
        self.editor_frame_label = editor_frame

        self.req_name_label = ttk.Label(editor_frame)
        self.req_name_label.pack(fill="x", padx=5, pady=(5, 0))
        self.editor_name_var = tk.StringVar()
        self.editor_name_var.trace_add("write", self.update_requirement_from_editor)
        self.editor_name_entry = ttk.Entry(editor_frame, textvariable=self.editor_name_var)
        self.editor_name_entry.pack(fill="x", padx=5, pady=2)

        needed_frame = ttk.Frame(editor_frame)
        needed_frame.pack(fill="x", padx=5, pady=5)
        self.needed_label = ttk.Label(needed_frame)
        self.needed_label.pack(side="left")
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
        self.add_course_btn = ttk.Button(add_remove_frame, command=self.add_course_to_requirement)
        self.add_course_btn.pack(pady=2, padx=20)
        self.remove_course_btn = ttk.Button(add_remove_frame, command=self.remove_course_from_requirement)
        self.remove_course_btn.pack(pady=2, padx=20)

        self.candidate_courses_label = ttk.Label(editor_frame)
        self.candidate_courses_label.pack(fill="x", padx=5)
        self.editor_candidates_listbox = tk.Listbox(editor_frame, selectmode="extended", exportselection=False)
        self.editor_candidates_listbox.pack(fill="both", expand=True, padx=5, pady=5)

    def _create_right_panel(self, parent_pane):
        """Builds the 'Program Requirements' and 'Quick Add' panel."""
        req_list_frame = ttk.LabelFrame(parent_pane)
        parent_pane.add(req_list_frame, width=300)
        self.req_list_frame_label = req_list_frame
        self.req_listbox = tk.Listbox(req_list_frame, exportselection=False)
        self.req_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.req_listbox.bind('<<ListboxSelect>>', self.on_req_select)
        req_btn_frame = ttk.Frame(req_list_frame)
        req_btn_frame.pack(fill="x", pady=5)
        self.new_req_btn = ttk.Button(req_btn_frame, command=self.create_new_requirement)
        self.new_req_btn.pack(side="left", expand=True, fill="x", padx=5)
        self.delete_req_btn = ttk.Button(req_btn_frame, command=self.delete_selected_requirement)
        self.delete_req_btn.pack(side="left", expand=True, fill="x", padx=5)

        adder_frame = ttk.LabelFrame(req_list_frame)
        adder_frame.pack(fill="x", padx=5, pady=10)
        self.adder_frame_label = adder_frame

        # --- MODIFIED: Create a container for the Treeview and Scrollbar ---
        tree_container = ttk.Frame(adder_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        # --- MODIFIED: Create the Scrollbar and link it ---
        tree_scrollbar = ttk.Scrollbar(tree_container, orient="vertical")
        tree_scrollbar.pack(side="right", fill="y")
        self.req_tree = ttk.Treeview(tree_container, show="tree", height=8, yscrollcommand=tree_scrollbar.set)
        self.req_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.config(command=self.req_tree.yview)

        # --- MODIFIED: Bind to the mouse click instead of the selection event ---
        self.req_tree.bind('<Button-1>', self.on_tree_click)
        self.req_tree.bind('<Double-1>', self.on_tree_double_click)

        # --- Create a frame for the action buttons ---
        action_button_frame = ttk.Frame(adder_frame)
        action_button_frame.pack(pady=5)

        self.add_template_btn = ttk.Button(action_button_frame, command=self.add_requirement_from_template)
        self.add_template_btn.pack(side="left", padx=5)

        self.expand_all_btn = ttk.Button(action_button_frame, command=self._expand_all_nodes)
        self.expand_all_btn.pack(side="left", padx=5)

        self.collapse_all_btn = ttk.Button(action_button_frame, command=self._collapse_all_nodes)
        self.collapse_all_btn.pack(side="left", padx=5)

    def _create_bottom_panel(self):
        """Builds the bottom navigation button bar."""
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", pady=10, side="bottom")
        self.back_btn = ttk.Button(bottom_frame, command=lambda: self.controller.show_screen1())
        self.back_btn.pack(side="left")
        self.continue_btn = ttk.Button(bottom_frame, command=self.continue_to_screen3)
        self.continue_btn.pack(side="right")
        self.save_json_btn = ttk.Button(bottom_frame, command=self.save_reqs)
        self.save_json_btn.pack(side="right", padx=10)
        self.load_last_btn = ttk.Button(bottom_frame, command=self.load_last_session)
        self.load_last_btn.pack(side="right", padx=10)
        self.load_json_btn = ttk.Button(bottom_frame, command=lambda: self.load_reqs())
        self.load_json_btn.pack(side="right")

    # --- NEW: Treeview control methods ---
    def _expand_all_nodes(self):
        """Expands all parent nodes in the Treeview."""
        for item_id in self.req_tree.get_children():
            self.req_tree.item(item_id, open=True)

    def _collapse_all_nodes(self):
        """Collapses all parent nodes in the Treeview."""
        for item_id in self.req_tree.get_children():
            self.req_tree.item(item_id, open=False)

    def update_text(self):
        """Update all text elements on this screen to the current language."""
        loc = self.loc
        self.title_label.config(text=loc.get_string('screen2_title'))
        self.courses_frame.config(text=loc.get_string('available_courses_label'))
        self.editor_frame_label.config(text=loc.get_string('edit_req_label'))
        self.req_name_label.config(text=loc.get_string('req_name_label'))
        self.needed_label.config(text=loc.get_string('needed_label'))
        self.add_course_btn.config(text=loc.get_string('add_selected_btn'))
        self.remove_course_btn.config(text=loc.get_string('remove_selected_btn'))
        self.candidate_courses_label.config(text=loc.get_string('candidate_courses_label'))
        self.req_list_frame_label.config(text=loc.get_string('program_reqs_label'))
        self.new_req_btn.config(text=loc.get_string('new_blank_req_btn'))
        self.delete_req_btn.config(text=loc.get_string('delete_selected_btn'))
        self.adder_frame_label.config(text=loc.get_string('quick_add_req_label'))

        # Update new and existing action buttons
        self.add_template_btn.config(text=loc.get_string('add_btn'))
        self.expand_all_btn.config(text=loc.get_string('expand_all_btn'))
        self.collapse_all_btn.config(text=loc.get_string('collapse_all_btn'))

        self.back_btn.config(text=loc.get_string('back'))
        self.continue_btn.config(text=loc.get_string('continue_to_config'))
        self.save_json_btn.config(text=loc.get_string('save_to_json'))
        self.load_last_btn.config(text=loc.get_string('load_last_session'))
        self.load_json_btn.config(text=loc.get_string('load_from_json'))

        # --- Rebuild the Treeview with translated names ---
        for i in self.req_tree.get_children():
            self.req_tree.delete(i)

        categories = {}
        # Map original English category names to their new localization keys
        cat_key_map = {
            "Business Administration": "cat_business",
            "Computer Science": "cat_cs",
            "General": "cat_general",
            "Anthropology": "cat_anth",
            "International Finance": "cat_baf",
            "Economics": "cat_econ",
            "Entrepreneurship": "cat_ent",
            "International Trade and Business": "cat_ibus",
            "International Relations": "cat_ir",
            "Management Information Systems": "cat_mis",
            "Psychology": "cat_psyc",
            "Law": "cat_law",
            "Artificial Intelligence and Data Engineering": "cat_ai",
            "Aviation Management": "cat_avm",
            "Civil Engineering": "cat_ce",
            "Communication Design": "cat_code",
            "Electrical and Electronics Engineering": "cat_ee",
            "Gastronomy and Culinary Arts": "cat_gca",
            "Hotel Management": "cat_hman",
            "Industrial Design": "cat_ide",
            "Industrial Engineering": "cat_ie",
            "Interior Architecture and Environmental Design": "cat_intar",
            "Professional Flight": "cat_plt",
        }

        # *** THIS IS THE CORRECTED LOOP ***
        for key, data in self.PREDEFINED_REQS_KEYS.items():
            cat_name = data["category"]
            if cat_name not in categories:
                cat_loc_key = cat_key_map[cat_name]  # e.g., "cat_business"
                translated_cat_name = loc.get_string(cat_loc_key)
                categories[cat_name] = self.req_tree.insert("", "end", text=translated_cat_name, open=True)

            translated_name = loc.get_string(key)
            # Store the language-independent KEY in values, but display the translated name
            self.req_tree.insert(categories[cat_name], "end", text=translated_name, values=(key,))

        # Add the custom file option, using a key
        self.req_tree.insert("", "end", text=loc.get_string('custom_file_option'), values=("custom_file",))

        for cat_id in categories.values():
            self.req_tree.item(cat_id, tags=('category',))
        self.req_tree.tag_configure('category', foreground='gray')

        # Refresh the main requirements listbox to reflect potential name changes
        self.update_req_listbox()

    def add_requirement_from_template(self):
        selected_item = self.req_tree.focus()
        if not selected_item:
            messagebox.showinfo(self.loc.get_string('info'), self.loc.get_string('select_template_msg'))
            return

        selection_key = self.req_tree.item(selected_item, "values")[0]

        if selection_key == "custom_file":
            filepath = filedialog.askopenfilename(title="Select Custom Course List File",
                                                  filetypes=(("Excel Files", "*.xls*"), ("All Files", "*.*")))
            if not filepath: return
            req_name = os.path.splitext(os.path.basename(filepath))[0]
            needed = "=1"
            self._create_req_from_file(filepath, req_name, needed)
        else:
            req_config = self.PREDEFINED_REQS_KEYS[selection_key]
            pre_reqs_path = self.controller.config.paths["pre_reqs_dir"]
            filepath = os.path.join(pre_reqs_path, req_config['folder'], req_config['file'])
            os.makedirs(os.path.join(pre_reqs_path, req_config['folder']), exist_ok=True)
            req_name = self.loc.get_string(selection_key)
            needed = req_config['needed']
            self._create_req_from_file(filepath, req_name, needed)

    def _create_req_from_file(self, filepath, req_name, needed_cond):
        try:
            df = pd.read_excel(filepath)

            # --- MODIFIED: Flexible column header check ---
            possible_headers = ['Ders', 'Course']
            valid_header = next((h for h in possible_headers if h in df.columns), None)

            if not valid_header:
                messagebox.showerror(self.loc.get_string('format_error_title'), self.loc.get_string('format_error_msg'))
                return

            # Use the header that was found
            base_codes = df[valid_header].dropna().astype(str).tolist()

            expanded_candidates = []
            all_offered_courses = self.controller.all_courses_list.keys()
            for base_code in base_codes:
                found_match = False
                for full_code in all_offered_courses:
                    if full_code.startswith(base_code + '.'):
                        expanded_candidates.append(full_code)
                        found_match = True
                if not found_match: print(f"Info: Base course '{base_code}' from the list had no offered sections.")

            if not expanded_candidates:
                messagebox.showwarning(
                    self.loc.get_string('warning'),
                    self.loc.get_string('no_offered_courses_warning', filename=os.path.basename(filepath))
                )

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

        # --- MODIFIED: Add validation for the number ---
        num = self.editor_needed_num_var.get()
        if not num.strip().isdigit():  # Check if it's not a number (handles empty strings too)
            num = "1"  # Default to 1 if invalid

        req['name'] = self.editor_name_var.get()
        req['needed'] = f"{self.editor_needed_op_var.get()}{num}"

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
            messagebox.showwarning(self.loc.get_string('warning'), self.loc.get_string('req_delete_warning'))
            return
        if messagebox.askyesno(self.loc.get_string('confirm_delete'), self.loc.get_string('confirm_delete_msg')):
            self.controller.requirements.pop(self.currently_editing_req_index)
            self.currently_editing_req_index = None
            self.update_req_listbox()
            self.clear_editor_panel()
            self.update_editor_panel_state()

    def add_course_to_requirement(self, event=None):
        if self.currently_editing_req_index is None:
            messagebox.showwarning(self.loc.get_string('warning'), self.loc.get_string('req_add_course_warning'))
            return
        selected_indices = self.course_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning(self.loc.get_string('warning'), self.loc.get_string('req_select_courses_warning'))
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
            messagebox.showwarning(self.loc.get_string('warning'), self.loc.get_string('req_remove_courses_warning'))
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
            messagebox.showinfo("Success", self.loc.get_string('reqs_saved_msg', filename=os.path.basename(path)))

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
                messagebox.showinfo("Success",
                                    self.loc.get_string('reqs_loaded_msg', count=len(self.controller.requirements)))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load or parse JSON file:\n{e}")

    def load_last_session(self):
        temp_req_path = os.path.join(self.controller.config.paths["reqs_dir"], "requirements_gui_temp.json")
        if not os.path.exists(temp_req_path):
            messagebox.showinfo(self.loc.get_string('info'), self.loc.get_string('no_last_session_msg'))
            return
        self.load_reqs(path=temp_req_path)

    def continue_to_screen3(self):
        if not self.controller.requirements:
            messagebox.showerror(self.loc.get_string('error'), self.loc.get_string('min_one_req_error'))
            return
        self.controller.config.requirements = self.controller.requirements
        temp_req_path = os.path.join(self.controller.config.paths["reqs_dir"], "requirements_gui_temp.json")
        with open(temp_req_path, 'w') as f: json.dump(self.controller.requirements, f)
        self.controller.config.input["requirements"]["basename"] = os.path.basename(temp_req_path)
        self.controller.show_screen3()

    def on_tree_click(self, event):
        """
        Prevents selection of category items, allowing the expand/collapse button to work.
        """
        item_id = self.req_tree.identify_row(event.y)
        if item_id and self.req_tree.tag_has('category', item_id):
            region = self.req_tree.identify_region(event.x, event.y)
            # Only block the event if the user clicks the text itself
            if region == "text":
                return "break"

    def on_tree_double_click(self, event):
        """Adds the double-clicked requirement to the list, with debouncing."""
        if self.double_click_locked:
            return
        selected_item_id = self.req_tree.focus()
        if not selected_item_id or self.req_tree.tag_has('category', selected_item_id):
            return
        self.double_click_locked = True
        self.add_requirement_from_template()
        DEBOUNCE_DELAY_MS = 500
        self.after(DEBOUNCE_DELAY_MS, self.unlock_double_click)

    def unlock_double_click(self):
        """Resets the double-click lock flag."""
        self.double_click_locked = False
