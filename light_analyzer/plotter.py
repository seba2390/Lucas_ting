# plotter.py

import matplotlib
# Force non-interactive backend BEFORE importing pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# Removed tk import as it's unused now
from .config import SMOOTHING_WINDOW
import os # For path joining

# Define a default save name
DEFAULT_PLOT_FILENAME = "analysis_plot.png"

class Plotter:
    def __init__(self, plot_frame): # plot_frame is no longer used here
        # self.plot_frame = plot_frame # No longer needed
        self.fig = None
        self.ax = None
        # Removed canvas_agg and plot_widget references

    def clear_plot(self):
        """Closes the current Matplotlib figure."""
        # Removed widget destruction code
        if self.fig:
            print("PLOTTER: Closing previous plot figure.") # DEBUG
            plt.close(self.fig)
            self.fig = None
            self.ax = None

    def plot_analysis(self, x_data, intensity_profile_db, # Changed argument name
                       valid_indices, smoothed_profile_db, # Added indices, changed smoothed name
                       fit_params):
        """Creates the analysis plot (dB scale) and saves it to a file."""
        print("PLOTTER: plot_analysis called (save mode - dB).") # DEBUG
        self.clear_plot() # Close previous figure

        if x_data is None or intensity_profile_db is None or valid_indices is None:
            print("Plotter: No valid dB data to plot.")
            return None

        # Use x_data corresponding to valid dB points
        x_plot_data = x_data[valid_indices]

        try:
            print("PLOTTER: Creating fig, ax...") # DEBUG
            self.fig, self.ax = plt.subplots(figsize=(6, 2.5))
            print(f"PLOTTER: Fig={self.fig}, Ax={self.ax}") # DEBUG

            # Plot raw dB data
            self.ax.plot(x_plot_data, intensity_profile_db, "b.", label="Intensity Data (dB)", markersize=4)

            # Plot smoothed dB data if available
            if smoothed_profile_db is not None and SMOOTHING_WINDOW > 1:
                 # Ensure smoothed data matches the valid x points
                 if len(smoothed_profile_db) == len(x_data):
                      smoothed_plot_data = smoothed_profile_db[valid_indices]
                      self.ax.plot(x_plot_data, smoothed_plot_data, "g-", label=f"Smoothed (w={SMOOTHING_WINDOW})", linewidth=1.5)
                 else:
                      print("Plotter Warning: Smoothed profile length mismatch, skipping plot.")

            # Plot linear fitted line
            if fit_params and 'r_squared' in fit_params and 'slope_db' in fit_params:
                slope_plot = fit_params['slope_db']
                intercept_plot = fit_params['intercept_db']
                rsq_plot = fit_params['r_squared']

                # Generate points for the fitted line across the valid x range
                fit_y = slope_plot * x_plot_data + intercept_plot

                # Create label for linear fit
                label = (
                    f"Linear Fit (dB): $y = mx + b$\n"
                    f"$m$={slope_plot:.4f} dB/unit, $b$={intercept_plot:.2f} dB, $R^2$={rsq_plot:.3f}"
                )
                self.ax.plot(x_plot_data, fit_y, "r-", label=label)

            self.ax.set_xlabel("Distance (units)")
            self.ax.set_ylabel("Relative Intensity (dB)")
            self.ax.set_title("Intensity Profile (dB scale) and Linear Fit")
            self.ax.legend(fontsize="small")
            self.ax.grid(True)
            self.fig.tight_layout()

            # --- Save the plot --- #
            save_path = os.path.abspath(DEFAULT_PLOT_FILENAME) # Save in current run dir
            try:
                print(f"PLOTTER: Saving plot to {save_path}") # DEBUG
                # Explicitly catch IOErrors and other save-related issues
                self.fig.savefig(save_path, dpi=150, bbox_inches='tight') # Added bbox_inches for potentially better layout saving
                print(f"PLOTTER: Plot saved successfully.")
                return save_path # Return path where saved
            except IOError as ioe:
                 print(f"PLOTTER: *** FAILED TO SAVE PLOT (IOError) *** to {save_path}: {ioe}")
                 print("PLOTTER: Check file permissions or if the directory exists and is writable.")
                 return None # Indicate save failure
            except Exception as save_e:
                 print(f"PLOTTER: *** FAILED TO SAVE PLOT (Other Error) *** to {save_path}: {type(save_e).__name__} - {save_e}")
                 return None # Indicate save failure
            finally:
                 # Close the figure after saving/attempting to save
                 self.clear_plot()

        except Exception as plot_e:
            print(f"Plotting failed before save: {plot_e}")
            self.clear_plot() # Ensure cleanup on error
            return None
