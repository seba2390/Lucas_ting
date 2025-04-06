# info_system.py

import numpy as np
from .config import INFO_R_SQUARED_THRESHOLD, INFO_SLOPE_NEAR_ZERO_THRESHOLD


def generate_feedback(fit_params, intensity_profile, x_data):
    """Generates feedback and suggestions based on fit results (dB slope) and data."""
    if not fit_params or 'r_squared' not in fit_params or 'slope_db' not in fit_params or intensity_profile is None:
        return "Analysis not complete or fit failed."

    r_squared = fit_params['r_squared']
    slope_db = fit_params['slope_db'] # This is alpha_db

    feedback = []

    # 1. R-squared Feedback (for linear fit on dB data)
    if r_squared < INFO_R_SQUARED_THRESHOLD:
        feedback.append(
            f"* Poor Linear Fit Quality (R² = {r_squared:.3f} < {INFO_R_SQUARED_THRESHOLD}):\n" \
            f"  The linear model doesn't fit the dB-scaled data well.\n" \
            f"  Suggestions:\n" \
            f"  - Check ROI Selection: Ensure the region shows consistent exponential behavior (linear in dB). Avoid non-exponential features (saturation, sharp peaks/dips, reflections)."
            f"  - Noise: High noise can obscure the linear trend in dB space."
            f"  - Verify Length: Ensure the entered physical length accurately matches the ROI width."
        )
    else:
        feedback.append(f"* Good Linear Fit Quality (R² = {r_squared:.3f}).")

    # 2. Slope (alpha_dB) Value Feedback
    if abs(slope_db) < INFO_SLOPE_NEAR_ZERO_THRESHOLD:
        feedback.append(
            f"* Near-Zero Slope (|m| ≈ {abs(slope_db):.2e} dB/unit):\n" \
            f"  The fitted change in dB is very small.\n" \
            f"  Suggestions:\n" \
            f"  - Check ROI: Little actual gain/loss, or region dominated by noise/non-exponential features."
            f"  - Increase Length/Signal Change: Analyze a longer section or image with clearer gain/loss."
        )
    elif slope_db > 0: # Positive slope in dB means increasing intensity (Gain)
        feedback.append(
             f"* Increasing Trend / Gain Fitted (Slope = {slope_db:.4f} dB/unit):\n" \
             f"  The fit indicates an increasing signal strength.\n" \
             f"  Suggestions:\n" \
             f"  - Verify Physics: Ensure gain is expected. If loss is expected, check ROI for reflections, scattering sources, detector non-linearities, etc."
        )
    else: # Negative slope_db means decreasing intensity (Loss)
         loss_alpha_db = -slope_db # Loss is positive value
         feedback.append(
             f"* Decreasing Trend / Loss Fitted (Slope = {slope_db:.4f} dB/unit):\n" \
             f"  The fit indicates signal loss (α_dB = {loss_alpha_db:.4f} dB/unit).\n" \
             f"  Suggestions:\n" \
             f"  - Consider Fit Quality (R²): If R² is low, the loss value might not be reliable."
        )

    # 3. Data Shape/Noise Feedback (Example)
    if len(intensity_profile) > 1:
        noise_metric = np.std(np.diff(intensity_profile)) # Simple noise estimate: std dev of differences
        signal_range = np.ptp(intensity_profile) # Peak-to-peak signal range
        if signal_range > 1e-9 and (noise_metric / signal_range) > 0.5: # If noise variation is large relative to signal range
             feedback.append(
                 f"* High Noise Detected:\n" \
                 f"  The intensity profile appears noisy relative to the overall signal change.\n" \
                 f"  Suggestions:\n" \
                 f"  - Image Quality: Use higher quality images if possible (less camera noise, better contrast)."
                 f"  - ROI Averaging: Ensure the ROI height includes enough pixels to average out noise vertically."
                 f"  - Smoothing: The visualization uses smoothing (green line); consider if stronger preprocessing (outside this tool) might be needed."
            )

    # 4. Check for Saturation (applied to original summed data)
    # Estimate max possible sum based on assumption of 8-bit source image
    # Note: This assumes the ROI height is implicitly included in the sum.
    # A better check might require knowing the ROI height if available.
    max_pixel_val = 255
    roi_height_estimate = 10 # Placeholder: If ROI height info was available, use it
    # max_possible_sum = max_pixel_val * roi_height_estimate * len(intensity_profile)
    # Simpler check based on max value in summed profile
    # This threshold is arbitrary without knowing image bit depth & ROI height
    # Adjust threshold based on typical summed values if needed.
    arbitrary_saturation_threshold = 60000 # Example threshold for summed value
    if np.max(intensity_profile) >= arbitrary_saturation_threshold:
        feedback.append(
            f"* Potential Saturation (High Summed Value):\n" \
            f"  Maximum summed intensity ({np.max(intensity_profile):.0f}) is high. Saturation may affect results.\n" \
            f"  Suggestions:\n" \
            f"  - Adjust Exposure/Gain during image capture."
            f"  - ROI Placement: Avoid regions appearing fully saturated."
            f"  - Check Bit Depth: Analysis assumes linear response; saturation breaks this."
        )

    if not feedback:
        return "Analysis complete. Fit appears reasonable based on R² and slope."

    return "\n\n".join(feedback)
