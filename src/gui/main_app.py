import tkinter as tk
from tkinter import ttk

from src.config import Config
from .screen1_setup import Screen1
from .screen2_builder import Screen2
from .screen3_generate import Screen3

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Course Program Generator")
        self.geometry("950x700")
        self.config = Config()
        self.config.update()  # Initial update to build paths
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