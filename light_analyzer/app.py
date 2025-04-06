# app.py

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import numpy as np
from PIL import Image

from .image_canvas import ImageCanvas
from .plotter import Plotter
from .analysis import (get_intensity_profile,
                     moving_average,
                     calculate_db_profile,
                     fit_linear_db,
                     calculate_r_squared_linear)
from .info_system import generate_feedback
from .config import DEFAULT_IMAGE_PATH, SMOOTHING_WINDOW


class LightAnalyzerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Light Loss Analyzer")
        self.master.geometry("1000x800") # Start with a decent size
        self.master.minsize(700, 500)

        # Data storage
        self.current_image_obj = None
        self.fit_params = None
        self.intensity_profile = None
        self.intensity_profile_db = None
        self.valid_db_indices = None
        self.smoothed_profile = None
        self.smoothed_profile_db = None
        self.x_data = None

        # UI References
        # Removed plot_widget_ref

        self._setup_ui()

    def _setup_ui(self):
        # --- Top Control Frame --- #
        control_frame = tk.Frame(self.master)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        btn_load = tk.Button(control_frame, text="Load Image", command=self._load_image_action)
        btn_load.pack(side=tk.LEFT, padx=5)

        btn_zoom_in = tk.Button(control_frame, text="+", command=lambda: self.image_canvas.zoom_in())
        btn_zoom_in.pack(side=tk.LEFT, padx=(10, 2))
        btn_zoom_out = tk.Button(control_frame, text="-", command=lambda: self.image_canvas.zoom_out())
        btn_zoom_out.pack(side=tk.LEFT, padx=(0, 10))

        lbl_length = tk.Label(control_frame, text="Length (units):")
        lbl_length.pack(side=tk.LEFT, padx=5)
        self.entry_length = tk.Entry(control_frame, width=10)
        self.entry_length.pack(side=tk.LEFT, padx=5)
        self.entry_length.insert(0, "1.0")

        self.btn_analyze = tk.Button(control_frame, text="Analyze", command=self._analyze_action, state=tk.DISABLED)
        self.btn_analyze.pack(side=tk.LEFT, padx=5)

        # --- Main Area Paned Window (Canvas/Info + Plot) --- #
        main_paned_window = tk.PanedWindow(self.master, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Top Pane (Canvas + Info Text) --- #
        top_pane = tk.PanedWindow(main_paned_window, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned_window.add(top_pane, stretch="always", minsize=200)

        # Canvas Frame (managed by ImageCanvas)
        canvas_frame = tk.Frame(top_pane, relief=tk.SUNKEN, borderwidth=1)
        top_pane.add(canvas_frame, stretch="always", width=600) # Give canvas initial width
        self.image_canvas = ImageCanvas(canvas_frame, status_callback=self._update_analyze_button_state)

        # Info Text Area Frame
        info_frame = tk.Frame(top_pane)
        top_pane.add(info_frame, stretch="never", width=300) # Give info initial width

        lbl_info = tk.Label(info_frame, text="Analysis Results & Feedback:", anchor="w")
        lbl_info.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))

        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=10, borderwidth=1, relief=tk.SUNKEN)
        self.info_text.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.insert(tk.END, "Load an image and select an ROI to begin.")
        self.info_text.config(state=tk.DISABLED) # Read-only

        # --- Bottom Pane (Plot Area Info) --- #
        # Frame no longer needs grid config or bg color
        plot_info_frame = tk.Frame(main_paned_window, relief=tk.SUNKEN, borderwidth=1)
        main_paned_window.add(plot_info_frame, stretch="always", height=50, minsize=40) # Reduced height
        # self.plotter = Plotter(plot_info_frame) # Plotter doesn't need frame reference now
        self.plotter = Plotter(None)

        # Add a label to inform user about plot saving
        self.lbl_plot_status = tk.Label(plot_info_frame, text="Plot will be saved as analysis_plot.png in the run directory.")
        self.lbl_plot_status.pack(padx=10, pady=10)

    def _update_analyze_button_state(self, roi_defined=False):
        """Callback from ImageCanvas to enable/disable Analyze button."""
        if roi_defined:
            self.btn_analyze.config(state=tk.NORMAL)
        else:
            self.btn_analyze.config(state=tk.DISABLED)
            self._clear_results()

    def _load_image_action(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff")])
        if not path:
            return
        self._load_image_from_path(path)

    def load_default_image(self):
        """Loads the image specified in config if it exists."""
        if DEFAULT_IMAGE_PATH and isinstance(DEFAULT_IMAGE_PATH, str) and len(DEFAULT_IMAGE_PATH) > 0:
            print(f"Loading default image: {DEFAULT_IMAGE_PATH}")
            self._load_image_from_path(DEFAULT_IMAGE_PATH)
        else:
            print("No valid default image path set in config.py. Use 'Load Image' button.")

    def _load_image_from_path(self, path):
        try:
            img = Image.open(path)
            self.current_image_obj = img # Keep reference if needed
            self.image_canvas.load_image(img)
            self._clear_results() # Clear previous results/plot
            self.info_text_update("Image loaded. Select ROI.")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found: {path}")
            self._clear_all()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self._clear_all()

    def _clear_all(self):
         """Clears image, results, plot, everything."""
         self.current_image_obj = None
         self.image_canvas.reset()
         self._clear_results()

    def _clear_results(self):
        """Clears analysis results, plot and info text."""
        self.fit_params = None
        self.intensity_profile = None
        self.intensity_profile_db = None
        self.valid_db_indices = None
        self.smoothed_profile = None
        self.smoothed_profile_db = None
        self.x_data = None
        self.plotter.clear_plot()
        # Removed plot widget clearing logic
        self.info_text_update("Select ROI and click Analyze.")
        # Update plot status label
        self.lbl_plot_status.config(text="Plot will be saved as analysis_plot.png in the run directory.")

    def info_text_update(self, text):
        """Helper to update the read-only info text area."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)

    def _analyze_action(self):
        if self.image_canvas.roi_coords is None:
            messagebox.showwarning("Warning", "Please select a Region of Interest (ROI) first.")
            return

        try:
            length = float(self.entry_length.get())
            if length <= 0:
                raise ValueError("Length must be positive.")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid length value: {e}")
            return

        self.info_text_update("Analyzing...")
        self.master.update_idletasks() # Refresh UI to show message

        try:
            # 1. Get Data
            roi_data = self.image_canvas.get_roi_data()
            if roi_data is None:
                raise ValueError("Could not extract data from ROI.")

            self.intensity_profile = get_intensity_profile(roi_data)
            if self.intensity_profile is None or len(self.intensity_profile) < 2:
                 raise ValueError("Intensity profile is empty or too short after processing.")

            # 2. Prepare X data
            roi_width_pixels = self.image_canvas.get_roi_width_pixels()
            if roi_width_pixels != len(self.intensity_profile):
                 print("Warning: ROI width mismatch vs profile length. Using profile length.")
                 roi_width_pixels = len(self.intensity_profile)
            self.x_data = np.linspace(0, length, roi_width_pixels)

            # 3. Normalize and Convert to dB
            self.intensity_profile_db, self.valid_db_indices = calculate_db_profile(self.intensity_profile)
            if self.intensity_profile_db is None:
                 raise ValueError("Could not convert intensity profile to dB.")
            # Filter x_data to match valid dB points for fitting
            x_data_db = self.x_data[self.valid_db_indices]

            # 4. Smooth raw data AND convert smoothed to dB (for visualization)
            if SMOOTHING_WINDOW > 1:
                self.smoothed_profile = moving_average(self.intensity_profile, SMOOTHING_WINDOW)
                # Convert smoothed profile to dB for plotting, using same valid indices logic
                self.smoothed_profile_db, _ = calculate_db_profile(self.smoothed_profile)
            else:
                 self.smoothed_profile = None
                 self.smoothed_profile_db = None

            # 5. Fit Linear Model to dB Data
            self.fit_params = fit_linear_db(x_data_db, self.intensity_profile_db)

            # 6. Calculate R-squared for the linear fit on dB data
            r_squared = calculate_r_squared_linear(x_data_db, self.intensity_profile_db, self.fit_params)
            if r_squared is not None:
                self.fit_params['r_squared'] = r_squared
            else:
                 self.fit_params['r_squared'] = np.nan

            # 7. Generate Results String & Feedback
            # Note: slope_db is alpha_db (loss/gain in dB/unit)
            results_text = (
                f"Loss/Gain (α_dB): {self.fit_params['slope_db']:.4f} dB/unit\n"
                f"Intercept (dB): {self.fit_params['intercept_db']:.2f} dB\n"
                f"R² (linear fit): {self.fit_params['r_squared']:.3f}"
            )
            feedback = generate_feedback(self.fit_params, self.intensity_profile, self.x_data)
            final_info = f"{results_text}\n\n--- Feedback & Suggestions ---\n{feedback}"
            self.info_text_update(final_info)

            # 8. Plot Results (dB scale)
            print("APP: Calling plotter.plot_analysis (save mode - dB)...") # DEBUG
            save_path = self.plotter.plot_analysis(self.x_data, # Pass full x_data
                                                   self.intensity_profile_db, # Pass dB profile
                                                   self.valid_db_indices, # Pass indices for mapping
                                                   self.smoothed_profile_db, # Pass smoothed dB profile
                                                   self.fit_params)
            print(f"APP: Plotter returned save path: {save_path}") # DEBUG

            # Update status label based on save result
            if save_path:
                 self.lbl_plot_status.config(text=f"Plot saved to: {save_path}")
            else:
                 self.lbl_plot_status.config(text="Failed to save plot.")

            print("APP: Finished analysis call.") # DEBUG

        except ValueError as ve:
             error_msg = f"Analysis Input Error: {ve}"
             messagebox.showerror("Analysis Error", error_msg)
             self.info_text_update(error_msg)
             self.plotter.clear_plot() # Ensure figure is closed even on non-convergence error
             # Try to plot original summed data if analysis failed partially
             # (No dB conversion or fit available here)
             self.plotter.clear_plot() # Clear any previous attempt
        except Exception as e:
            error_msg = f"Unexpected Analysis Error: {e}"
            messagebox.showerror("Analysis Error", error_msg)
            self.info_text_update(error_msg)
            self.plotter.clear_plot() # Ensure figure is closed even on non-convergence error
            # Try to plot original summed data if analysis failed partially
            # (No dB conversion or fit available here)
            self.plotter.clear_plot() # Clear any previous attempt
            import traceback
            traceback.print_exc() # Print full traceback to console for debugging
