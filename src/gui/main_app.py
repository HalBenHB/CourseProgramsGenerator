import tkinter as tk
from tkinter import ttk
import webbrowser
from urllib.parse import quote_plus

from src.config import Config
from src.localization import LocalizationManager
from .screen1_setup import Screen1
from .screen2_builder import Screen2
from .screen3_generate import Screen3
from .widgets import FeedbackDialog

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.loc = LocalizationManager()
        self.loc.register(self.update_text) # Register App's own text updater

        self.geometry("950x700")

        # --- NEW: Disable the maximize button and resizing ---
        self.resizable(False, False)

        self.config = Config()
        self.config.loc = self.loc # Attach localization manager to config
        self.config.update()  # Initial update to build paths
        self.all_courses_list = {}
        self.requirements = []

        # --- Top Bar Frame (for Language and Feedback) ---
        top_bar_frame = ttk.Frame(self)
        top_bar_frame.pack(fill="x", padx=10, pady=(5, 0))

        # Language Switcher
        ttk.Label(top_bar_frame, text="Language:").pack(side="left")
        self.lang_btn_en = ttk.Button(top_bar_frame, text="English", command=lambda: self.loc.set_language('en'))
        self.lang_btn_en.pack(side="left", padx=5)
        self.lang_btn_tr = ttk.Button(top_bar_frame, text="Türkçe", command=lambda: self.loc.set_language('tr'))
        self.lang_btn_tr.pack(side="left")

        # --- MODIFIED: The button now opens our custom dialog ---
        self.feedback_button = ttk.Button(top_bar_frame, command=self.show_feedback_dialog)
        self.feedback_button.pack(side="right")

        # --- Main Container for Screens ---
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        self.frames = {}
        for F in (Screen1, Screen2, Screen3):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            self.loc.register(frame.update_text) # Register each screen for updates

        self.update_text() # Set initial texts
        self.show_frame(Screen1)

    def show_feedback_dialog(self):
        """Creates and shows the custom feedback dialog."""
        dialog = FeedbackDialog(self, self.loc, "halil.nebioglu@ozu.edu.tr")

    def open_feedback_email(self):
        """Opens the user's default email client with pre-filled fields."""
        recipient = "halil.nebioglu@ozu.edu.tr"
        subject = "Course Program Generator"

        # URL-encode the subject to handle spaces and special characters
        encoded_subject = quote_plus(subject)

        # Construct the mailto link
        mailto_url = f"mailto:{recipient}?subject={encoded_subject}"

        # Open the link in the default mail client
        webbrowser.open(mailto_url)

    def update_text(self):
        """Updates the text for the main application window."""
        self.title(self.loc.get_string('app_title'))

        # Update language button state
        if self.loc.current_language == 'en':
            self.lang_btn_en.config(state="disabled")
            self.lang_btn_tr.config(state="normal")
        else:
            self.lang_btn_en.config(state="normal")
            self.lang_btn_tr.config(state="disabled")

        # Update feedback button text
        self.feedback_button.config(text=self.loc.get_string('feedback_btn'))

    def toggle_lang_buttons(self, enabled=True):
        """Enables or disables the language switching buttons."""
        state = "normal" if enabled else "disabled"
        self.lang_btn_en.config(state=state)
        self.lang_btn_tr.config(state=state)
        # After changing state, call update_text to correctly disable the active one
        if enabled:
            self.update_text()

    def show_frame(self, page_name): self.frames[page_name].tkraise()
    def get_frame(self, page_name): return self.frames[page_name]

    def show_screen1(self):
        self.show_frame(Screen1)

    def show_screen2(self):
        self.show_frame(Screen2)

    def show_screen3(self):
        self.show_frame(Screen3)

    def on_courses_loaded(self):
        """
        This method is called by Screen1 after courses are successfully loaded.
        It handles the logic of updating Screen2 and switching the view.
        """
        # Get the Screen2 frame instance using its class as the key
        screen2_frame = self.get_frame(Screen2)

        # Get the list of course names from the stored data
        course_names = list(self.all_courses_list.keys())

        # Call the update method on the Screen2 frame
        screen2_frame.update_course_list(course_names)

        # Finally, switch to the Screen2 frame
        self.show_frame(Screen2)


# This file is now the main entry point for the GUI
if __name__ == "__main__":
    app = App()
    app.mainloop()