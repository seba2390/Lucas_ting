# analysis.py

import numpy as np


# ---------------------------
# Data Extraction and Processing
# ---------------------------

def get_intensity_profile(roi_image_data):
    """Calculates the vertical sum of pixel intensities."""
    if roi_image_data is None or roi_image_data.size == 0:
        return None
    return np.sum(roi_image_data, axis=0).astype(np.float64)

def moving_average(data, window_size):
    """Applies a moving average filter to the data."""
    if window_size < 1 or window_size % 2 == 0:
        # Return original data if window is invalid/disabled
        if window_size != 1:
            print(f"Warning: Invalid smoothing window {window_size}. Must be odd and >= 1. Smoothing disabled.")
        return data
    if len(data) < window_size:
        # Not enough data for the window
        return data

    # Pad edges to handle boundaries during convolution
    pad_size = window_size // 2
    padded_data = np.pad(data, pad_size, mode='edge')
    weights = np.ones(window_size) / window_size
    smoothed = np.convolve(padded_data, weights, mode='valid')
    return smoothed

# ---------------------------
# Fitting Functions (Now Linear Fit on dB data)
# ---------------------------

def calculate_db_profile(intensity_profile):
    """Normalizes profile to its peak and converts to dB."""
    if intensity_profile is None or len(intensity_profile) == 0:
        return None, None # Return None for profile and indices

    peak_intensity = np.max(intensity_profile)
    if peak_intensity <= 1e-9: # Avoid division by zero or log(0)
        print("Warning: Peak intensity is near zero. Cannot calculate dB profile.")
        return None, None

    normalized_profile = intensity_profile / peak_intensity

    # Filter for dB calculation (intensity > 0)
    valid_indices = np.where(normalized_profile > 1e-9)[0] # Use small threshold > 0
    if len(valid_indices) == 0:
        print("Warning: No positive intensity values after normalization. Cannot calculate dB profile.")
        return None, None

    profile_db = 10 * np.log10(normalized_profile[valid_indices])

    return profile_db, valid_indices


def fit_linear_db(x_data, profile_db):
    """Fits y = mx + b to the dB profile vs distance using polyfit."""
    if x_data is None or profile_db is None or len(x_data) != len(profile_db) or len(x_data) < 2:
        raise ValueError("Insufficient or mismatched data for linear dB fitting.")

    try:
        # Perform linear regression (degree 1 polynomial fit)
        slope, intercept = np.polyfit(x_data, profile_db, 1)

        # Fit parameters: slope is alpha_db (loss/gain in dB/unit length), b is intercept
        fit_params = {'slope_db': slope, 'intercept_db': intercept}
        print(f"Linear dB Fit Results: [Slope={slope:.4f} dB/unit, Intercept={intercept:.2f} dB]")
        return fit_params

    except Exception as e:
         print(f"Unexpected linear fitting error: {e}")
         raise RuntimeError(f"An unexpected error occurred during linear dB fitting: {e}") from e


# ---------------------------
# Goodness-of-Fit
# ---------------------------

def calculate_r_squared_linear(x_data, y_data, fit_params):
    """Calculates the R-squared value for the linear dB fit."""
    if not fit_params or 'slope_db' not in fit_params or x_data is None or y_data is None or len(x_data) == 0:
        return None
    try:
        slope = fit_params['slope_db']
        intercept = fit_params['intercept_db']
        fitted_func = lambda x: slope * x + intercept
        residuals = y_data - fitted_func(x_data)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        if ss_tot <= 1e-15:
            return 1.0 if ss_res < 1e-15 else 0.0
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
    except Exception as e:
        print(f"Error calculating R-squared for linear fit: {e}")
        return None
