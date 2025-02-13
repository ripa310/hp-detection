import os
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
import tkinter as tk
from tkinter import messagebox
import json
import vlc

# Set the path to Tesseract executable (update this path to where you installed Tesseract)
pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract\tesseract.exe'

# Global variables for HP bar region and threshold
hp_bar_region = None
hp_threshold = 0.65  # 30% HP threshold
calibration_file = "calibration.json"  # File to store the calibration data

def load_calibration():
    """Load the HP bar region from a calibration file."""
    global hp_bar_region
    if os.path.exists(calibration_file):
        with open(calibration_file, "r") as f:
            hp_bar_region = tuple(json.load(f))
        print(f"Loaded HP bar region from calibration: {hp_bar_region}")
    else:
        print("No previous calibration found. Please calibrate.")

def save_calibration():
    """Save the HP bar region to a calibration file."""
    if hp_bar_region:
        with open(calibration_file, "w") as f:
            json.dump(list(hp_bar_region), f)
        print(f"HP bar region saved to {calibration_file}")
    else:
        print("Calibration failed. No region to save.")

def calibrate_hp_bar():
    """Calibrate the HP bar region using a rectangle drawn by the user."""
    global hp_bar_region

    def on_mouse_down(event):
        global start_x, start_y, rect
        start_x, start_y = event.x, event.y
        # Create a rectangle on the canvas
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)

    def on_mouse_drag(event):
        global rect
        # Update the rectangle as the mouse is dragged
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        global hp_bar_region
        end_x, end_y = event.x, event.y
        # Ensure the coordinates are in the correct order (top-left to bottom-right)
        hp_bar_region = (
            min(start_x, end_x),
            min(start_y, end_y),
            max(start_x, end_x),
            max(start_y, end_y),
        )
        root.destroy()
        save_calibration()  # Save the calibration to file

    root = tk.Tk()
    root.title("Calibrate HP Bar")
    root.attributes("-fullscreen", True)  # Fullscreen to capture the entire screen
    root.attributes("-alpha", 0.5)  # Make the window semi-transparent
    canvas = tk.Canvas(root)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Bind mouse events
    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    root.mainloop()

    if hp_bar_region:
        messagebox.showinfo("Calibration Complete", f"HP bar region set to: {hp_bar_region}")
    else:
        messagebox.showerror("Error", "Calibration failed. Please try again.")

def capture_hp_bar():
    """Capture the HP bar region based on the calibrated rectangle."""
    if not hp_bar_region:
        raise ValueError("HP bar region not calibrated. Please run calibration first.")

    screenshot = ImageGrab.grab(bbox=hp_bar_region)
    return screenshot

def save_image(image, filename="captured_hp_bar.png"):
    """Save and overwrite the image."""
    # Save or overwrite the image with the specified filename
    image.save(filename)
    print(f"Image saved as '{filename}'")


def extract_hp_value(image):
    """Extract the HP value from the image using OCR."""
    # Preprocess the image
    save_image(image)
    # Extract text from the image using OCR
    custom_config = r'--oem 3 --psm 6 outputbase digits'
    text = pytesseract.image_to_string(image, config=custom_config)
    print(f"Extracted text: {text}")  # Debugging the extracted text

    # Clean up the text (remove non-numeric characters if any)
    text = ''.join(filter(str.isdigit, text))

    # Split the text into current HP and max HP (after every 6 characters)
    if len(text) >= 12:  # Ensure that the text has at least 12 digits
        current_hp = int(text[:6])  # First 6 digits
        max_hp = int(text[6:12])  # Next 6 digits
        return current_hp, max_hp
    else:
        print("Failed to extract valid HP values.")
        return None, None


def check_hp():
    """Check the HP and play a sound if below the threshold."""
    screenshot = capture_hp_bar()
    current_hp, max_hp = extract_hp_value(screenshot)
    print(current_hp)
    if current_hp is not None and max_hp is not None:
        hp_percentage = current_hp / max_hp
        print(f"Current HP: {current_hp}/{max_hp} ({hp_percentage * 100:.2f}%)")

        if hp_percentage < hp_threshold:
            print("HP is below threshold! Playing alert sound...")
            p = vlc.MediaPlayer('calm.mp3')  # Replace with your sound file path
            p.play()
    else:
        print("Failed to read HP value.")

def main():
    # Load calibration if exists
    load_calibration()

    # If no calibration is loaded, calibrate the HP bar region
    if not hp_bar_region:
        calibrate_hp_bar()

    # Main loop to monitor HP
    try:
        while True:
            check_hp()
            pyautogui.sleep(1)  # Check every second
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()
