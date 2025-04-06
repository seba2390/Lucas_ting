# Configuration Constants

# Set the default image path here. Leave as None or empty string to use the file dialog.
DEFAULT_IMAGE_PATH = "chatgpt.png"  # <<< SET YOUR IMAGE PATH HERE

# Display settings
MAX_DISPLAY_WIDTH = 1200
MAX_DISPLAY_HEIGHT = 800
MIN_ZOOM_LEVEL = 0.1
ZOOM_FACTOR = 1.2

# Analysis settings
SMOOTHING_WINDOW = 5  # Size of moving average window (used for visualization only now)

# Info System thresholds
INFO_R_SQUARED_THRESHOLD = 0.5 # R^2 below this is considered a poor fit
# Check if the dB slope is close to zero
INFO_SLOPE_NEAR_ZERO_THRESHOLD = 1e-2 # Threshold for |slope| in dB/unit length
