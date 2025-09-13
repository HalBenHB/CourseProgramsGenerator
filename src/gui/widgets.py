import tkinter as tk
from tkinter import ttk

class FeedbackDialog(tk.Toplevel):
    """A custom dialog for providing feedback options."""
    def __init__(self, parent, loc_manager, email_address):
        super().__init__(parent)
        self.loc = loc_manager
        self.email_address = email_address
        self.parent = parent # The main App window

        # Center the dialog over the main window
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        self.geometry(f"380x150+{parent_x + (parent_width // 2) - 190}+{parent_y + (parent_height // 2) - 75}")

        self.resizable(False, False)
        self.transient(parent) # Keep dialog on top
        self.grab_set() # Modal behavior

        # --- Widgets ---
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)

        self.instruction_label = ttk.Label(main_frame, wraplength=350, justify="center")
        self.instruction_label.pack(pady=(0, 10))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)

        self.open_email_btn = ttk.Button(button_frame, command=self.open_email_app)
        self.open_email_btn.pack(side="left", padx=5)

        self.copy_email_btn = ttk.Button(button_frame, command=self.copy_to_clipboard)
        self.copy_email_btn.pack(side="left", padx=5)

        self.copied_label = ttk.Label(main_frame, foreground="blue")
        self.copied_label.pack(pady=(5, 0))

        self.update_text() # Set initial text

    def update_text(self):
        """Updates all text in the dialog to the current language."""
        self.title(self.loc.get_string('feedback_title'))
        self.instruction_label.config(text=self.loc.get_string('feedback_instruction'))
        self.open_email_btn.config(text=self.loc.get_string('feedback_open_email_btn'))
        self.copy_email_btn.config(text=self.loc.get_string('feedback_copy_email_btn'))

    def open_email_app(self):
        # This function is now passed from main_app
        self.parent.open_feedback_email()
        self.destroy()

    def copy_to_clipboard(self):
        """Copies the email address to the system clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.email_address)
        self.update() # Ensure clipboard is updated

        # Show confirmation message
        self.copied_label.config(text=self.loc.get_string('feedback_copied_confirm'))

        # Make the dialog disappear after a short delay
        self.after(1200, self.destroy)


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
        label = tk.Label(self.tooltip_window, text=self.text, justify='left', bg="#ffffe0", relief='solid',
                         borderwidth=1, font=("tahoma", "8", "normal"))
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
