# main.py

import tkinter as tk
from light_analyzer.app import LightAnalyzerApp

def main():
    """Creates the main window and starts the Tkinter event loop."""
    root = tk.Tk()
    app = LightAnalyzerApp(root)
    # Try loading the default image specified in config
    app.load_default_image()
    root.mainloop()

if __name__ == "__main__":
    main()
