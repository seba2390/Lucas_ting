# image_canvas.py

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from .config import MAX_DISPLAY_WIDTH, MAX_DISPLAY_HEIGHT, MIN_ZOOM_LEVEL, ZOOM_FACTOR
import numpy as np

class ImageCanvas:
    def __init__(self, master_frame, status_callback=None):
        self.canvas_frame = master_frame
        self.status_callback = status_callback # Function to call when ROI changes

        self.original_image = None
        self.display_image_obj = None # Base image for canvas (potentially downscaled)
        self.tk_image = None # PhotoImage currently displayed
        self.display_scale_factor = 1.0 # original -> display_image_obj
        self.canvas_zoom_level = 1.0 # display_image_obj -> canvas view

        self.roi_coords = None # Coords relative to ORIGINAL image (x1, y1, x2, y2)
        self.roi_rect_id = None # ID of the rectangle on the canvas

        self.start_x = None
        self.start_y = None

        self._setup_widgets()
        self._bind_events()

    def _setup_widgets(self):
        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, cursor="cross", background="#CCCCCC") # Lighter gray

        # Scrollbars
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Grid layout
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)
        # Optional: Bind mouse wheel for zooming (platform dependent)
        # self.canvas.bind("<MouseWheel>", self._on_mouse_wheel) # Windows
        # self.canvas.bind("<Button-4>", lambda e: self.zoom_in()) # Linux scroll up
        # self.canvas.bind("<Button-5>", lambda e: self.zoom_out()) # Linux scroll down

    def load_image(self, image_object: Image.Image):
        """Loads a PIL Image object, prepares display version, and redraws."""
        if image_object is None:
            self.reset()
            return
        try:
            self.original_image = image_object.convert("L") # Ensure grayscale
            self.canvas_zoom_level = 1.0
            self._prepare_display_image()
            self.redraw_canvas()
            self.reset_roi()
        except Exception as e:
             messagebox.showerror("Error", f"Failed to process image for canvas: {e}")
             self.reset()

    def reset(self):
        """Resets the canvas and all related image/ROI data."""
        self.original_image = None
        self.display_image_obj = None
        self.tk_image = None
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, 0, 0))
        self.reset_roi()

    def reset_roi(self):
        """Resets only the ROI data and visual rectangle."""
        self.roi_coords = None
        if self.roi_rect_id:
            self.canvas.delete(self.roi_rect_id)
            self.roi_rect_id = None
        self.start_x = None
        self.start_y = None
        if self.status_callback:
            self.status_callback(roi_defined=False)

    def _prepare_display_image(self):
        """Creates the potentially downscaled base image for display."""
        if not self.original_image:
            self.display_image_obj = None
            self.display_scale_factor = 1.0
            return

        orig_width, orig_height = self.original_image.size
        self.display_scale_factor = 1.0
        self.display_image_obj = self.original_image.copy()

        if orig_width > MAX_DISPLAY_WIDTH or orig_height > MAX_DISPLAY_HEIGHT:
            width_scale = MAX_DISPLAY_WIDTH / orig_width
            height_scale = MAX_DISPLAY_HEIGHT / orig_height
            scale = min(width_scale, height_scale)
            display_width = int(orig_width * scale)
            display_height = int(orig_height * scale)
            # Use ANTIALIAS for better quality downscaling
            self.display_image_obj = self.display_image_obj.resize((display_width, display_height), Image.Resampling.LANCZOS)
            # Recalculate scale factor accurately based on actual resize
            self.display_scale_factor = orig_width / self.display_image_obj.width

    def redraw_canvas(self):
        """Redraws the canvas with the image at the current zoom level."""
        if not self.display_image_obj:
            self.canvas.delete("all")
            self.canvas.config(scrollregion=(0,0,0,0))
            return

        zoomed_width = int(self.display_image_obj.width * self.canvas_zoom_level)
        zoomed_height = int(self.display_image_obj.height * self.canvas_zoom_level)
        zoomed_width = max(1, zoomed_width)
        zoomed_height = max(1, zoomed_height)

        try:
            zoomed_display_image = self.display_image_obj.resize(
                (zoomed_width, zoomed_height), Image.Resampling.NEAREST # Use NEAREST for zoom speed
            )
            self.tk_image = ImageTk.PhotoImage(zoomed_display_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            self.canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))
            self._redraw_roi_rect() # Redraw ROI scaled to new zoom

        except Exception as e:
            print(f"Error during canvas redraw: {e}")
            # Consider showing a visual indicator of error on canvas

    def _redraw_roi_rect(self):
        """Redraws the ROI rectangle based on roi_coords and current zoom/scale."""
        if self.roi_rect_id:
            self.canvas.delete(self.roi_rect_id)
            self.roi_rect_id = None

        if self.roi_coords and self.display_image_obj:
            try:
                # Convert original ROI coords -> zoomed canvas coordinates
                orig_x1, orig_y1, orig_x2, orig_y2 = self.roi_coords
                disp_x1 = orig_x1 / self.display_scale_factor
                disp_y1 = orig_y1 / self.display_scale_factor
                disp_x2 = orig_x2 / self.display_scale_factor
                disp_y2 = orig_y2 / self.display_scale_factor
                zoomed_x1 = disp_x1 * self.canvas_zoom_level
                zoomed_y1 = disp_y1 * self.canvas_zoom_level
                zoomed_x2 = disp_x2 * self.canvas_zoom_level
                zoomed_y2 = disp_y2 * self.canvas_zoom_level

                self.roi_rect_id = self.canvas.create_rectangle(
                    zoomed_x1, zoomed_y1, zoomed_x2, zoomed_y2, outline="#FF0000", width=2 # Bright red
                )
            except Exception as e:
                 print(f"Error redrawing ROI rectangle: {e}")

    # --- Event Handlers --- #

    def _on_button_press(self, event):
        if not self.display_image_obj:
            return
        self.reset_roi()
        # Convert view coords to canvas coords (considering scrollbars)
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # Create rectangle, initially small
        self.roi_rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x + 1, self.start_y + 1, outline="#FF0000", width=2
        )

    def _on_mouse_drag(self, event):
        if not self.roi_rect_id or self.start_x is None or self.start_y is None:
            return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        # Update ROI rectangle visually
        self.canvas.coords(self.roi_rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def _on_button_release(self, event):
        if not self.roi_rect_id or self.start_x is None or self.start_y is None or not self.original_image:
            self.reset_roi()
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Canvas coordinates of the drawn rectangle
        canvas_x1 = min(self.start_x, end_x)
        canvas_y1 = min(self.start_y, end_y)
        canvas_x2 = max(self.start_x, end_x)
        canvas_y2 = max(self.start_y, end_y)

        # --- Coordinate Scaling: Canvas -> Original Image --- #
        try:
            # Scale from zoomed canvas to base display coordinates
            disp_x1 = canvas_x1 / self.canvas_zoom_level
            disp_y1 = canvas_y1 / self.canvas_zoom_level
            disp_x2 = canvas_x2 / self.canvas_zoom_level
            disp_y2 = canvas_y2 / self.canvas_zoom_level

            # Scale from display coordinates to original image coordinates
            orig_x1 = int(disp_x1 * self.display_scale_factor)
            orig_y1 = int(disp_y1 * self.display_scale_factor)
            orig_x2 = int(disp_x2 * self.display_scale_factor)
            orig_y2 = int(disp_y2 * self.display_scale_factor)

            # Clamp scaled coordinates to the ORIGINAL image bounds
            orig_img_width, orig_img_height = self.original_image.size
            orig_x1 = max(0, orig_x1)
            orig_y1 = max(0, orig_y1)
            orig_x2 = min(orig_img_width, orig_x2)
            orig_y2 = min(orig_img_height, orig_y2)

            # Check for valid ROI size in original coordinates
            if orig_x1 >= orig_x2 or orig_y1 >= orig_y2:
                print("ROI too small or invalid after scaling.")
                self.reset_roi()
                return

            # Store the valid ROI coordinates (relative to ORIGINAL image)
            self.roi_coords = (orig_x1, orig_y1, orig_x2, orig_y2)
            # Update the visual rectangle to final canvas coords
            self.canvas.coords(self.roi_rect_id, canvas_x1, canvas_y1, canvas_x2, canvas_y2)
            print(f"ROI Set (Original Coords): {self.roi_coords}")
            if self.status_callback:
                 self.status_callback(roi_defined=True)

        except Exception as e:
             print(f"Error processing ROI coordinates: {e}")
             self.reset_roi()

    # --- Zoom Control Methods --- #
    def zoom_in(self):
        if not self.display_image_obj: return
        self.canvas_zoom_level *= ZOOM_FACTOR
        self.redraw_canvas()

    def zoom_out(self):
        if not self.display_image_obj: return
        next_zoom = self.canvas_zoom_level / ZOOM_FACTOR
        if next_zoom < MIN_ZOOM_LEVEL:
            self.canvas_zoom_level = MIN_ZOOM_LEVEL
        else:
            self.canvas_zoom_level = next_zoom
        self.redraw_canvas()

    def get_roi_data(self):
         """Crops the original image based on the current ROI coords."""
         if self.roi_coords and self.original_image:
             try:
                 return np.array(self.original_image.crop(self.roi_coords))
             except Exception as e:
                  print(f"Error cropping ROI: {e}")
                  return None
         return None

    def get_roi_width_pixels(self):
         """Returns the width of the ROI in original image pixels."""
         if self.roi_coords:
             return self.roi_coords[2] - self.roi_coords[0]
         return 0
