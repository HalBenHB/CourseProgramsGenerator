from src.gui.main_app import App
import sys
import os

# This ensures that the 'src' directory is in Python's path,
# which helps with resolving modules correctly.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    app = App()
    app.mainloop()