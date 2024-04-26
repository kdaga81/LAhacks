from __future__ import annotations
import time
from pathlib import Path
from urllib.request import urlopen
from PIL import Image
from typing import Optional

import google.generativeai as genai 
import os
import reflex as rx
import reflex_webcam as webcam

# Configure the generative AI API
genai.configure(api_key="AIzaSyCasxpYtiSqL6Mbe9uMa5Q0eYR3p5MZNCQ")
model = genai.GenerativeModel('gemini-pro-vision')

# Identifies a particular webcam component in the DOM
WEBCAM_REF = "webcam"

# Dictionary mapping item numbers to item names
item_mapping = {
    "0": "Please Try Again",
    "1": "Scissor",
    "2": "Forceps",
    "3": "Needle Holder",
    "4": "Scalpel",
    "5": "Retractor",
    "6": "Babcock Forceps",
    "7": "Surgical tables",
    "8": "Surgical Cannula",
    "9": "Blade",
    # Add more key-value pairs as needed
}

class State(rx.State):
    last_screenshot: Optional[Image.Image] = None
    last_screenshot_timestamp: str = ""
    last_screenshot_response_text: str = "" 
    loading: bool = False
    captured_data: list[tuple] = []
    timer_label: str = ""
    removal_mode: bool = False

    def handle_screenshot(self, img_data_uri: str):
        """Webcam screenshot upload handler."""
        if self.loading:
            return
        self.last_screenshot_timestamp = time.strftime("%H:%M:%S %p")
        with urlopen(img_data_uri) as img:
            self.last_screenshot = Image.open(img)
            response = model.generate_content(["Just write the number in the image", self.last_screenshot])
            response.resolve()
            # Check if response text is greater than 20 characters
            if len(response.text) > 2:
                self.last_screenshot_response_text = "0"
            else:
                self.last_screenshot_response_text = response.text
            # self.last_screenshot_response_text = response.text
            self.last_screenshot.load()
            folder_path = os.path.join(os.path.dirname(__file__), "screenshots")
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, f"{self.last_screenshot_response_text}_{self.last_screenshot_timestamp}.jpeg")
            self.last_screenshot.save(file_path, format="JPEG")
            # Append captured data to the list
            print("handle")
            print("Last screenshot response text:", self.last_screenshot_response_text)
            if self.removal_mode and self.last_screenshot_response_text:
                print("Removing data with response text:", self.last_screenshot_response_text)
                testbuff = []
                for data in self.captured_data:
                    print(data[2])
                    print(self.last_screenshot_response_text.strip())
                    print(data[2] == self.last_screenshot_response_text.strip())
                    if data[2] == self.last_screenshot_response_text.strip():
                        self.captured_data.remove(data)

                # print(testbuff)
                # self.captured_data = [data for data in self.captured_data if data[2] != self.last_screenshot_response_text]
                print("Captured data after removal:", self.captured_data)
            else:
                print("Data:", self.last_screenshot_response_text.strip())
                print("ItemMap:", item_mapping)
                self.captured_data.insert(0,(self.last_screenshot, self.last_screenshot_timestamp, self.last_screenshot_response_text.strip(), item_mapping.get(self.last_screenshot_response_text.strip(), "Unknown1")))
            print(self.captured_data)
            # Remove photos with specific response text if removal mode is enabled
            # self.remove_captured_data()

    def toggle_removal_mode(self):
        self.removal_mode = not self.removal_mode
        print("Removal mode enabled:", self.removal_mode)
        # Remove photos with specific response text if removal mode is enabled
        self.remove_captured_data()

    def remove_captured_data(self):
        """Remove photos with specific response text."""
        if self.removal_mode:
            # Remove photos with the specified response text
            self.captured_data = [data for data in self.captured_data if data[2] != self.last_screenshot_response_text]


def webcam_upload_component(ref: str) -> rx.Component:
    """Component for displaying webcam preview and uploading screenshots."""

    return rx.vstack(
        webcam.webcam(
            id=ref,
            on_click=webcam.upload_screenshot(
                ref=ref,
                handler=State.handle_screenshot,  # type: ignore
            ),
        ),
            # Toggle removal button
        rx.center(
            rx.button(
                "Let's Operate",
                on_click=State.toggle_removal_mode,
                style={"margin-left": "240px"} 
            ),
        )

    )


def display_captured_data(data: tuple, item_mapping: dict):
    item_number = data[2]
    print("display")
    print(item_number)

           
    item_name = item_mapping.get(item_number, "Unknown")
    return rx.box(
            rx.fragment(
                rx.image(src=data[0]),
                rx.text(f"Time: {data[1]}"),
                rx.text(f"Item Number: {data[2]}"),
                rx.text(f"Item Name: {data[3]}"),
            ),
            style={"display": "inline-block", "margin": "10px", "height": "200px", "width": "200px"}
    )

def header():
    return rx.vstack(
        rx.hstack(
            rx.fragment(
                rx.image(src="/logo.jpeg", width="8em", height="5em"),
            ),
            rx.fragment(
                rx.text("Track your Surgical tools💉!", color="white", font_size="3em", margin_left="1em"),  # Adjust text as needed
            ),
        ),
        position="fixed",
        width="100%",
        left="0px",
        top="0px",
        z_index="5",
        padding_x="0.5em",
        padding_y="0.5em",
        background_color="black",
        align_items="left",
        height="100px",
    )

def index() -> rx.Component:
    """Main component of the application."""
    return rx.fragment(
        header(),
        rx.center(
            webcam_upload_component(WEBCAM_REF),
            padding_top="8em",
        ),
        rx.hstack(
            rx.foreach(
                State.captured_data, 
                lambda data: display_captured_data(data, item_mapping),
            ),
            padding_top="3em",
        ),
    )


# Initialize the application
app = rx.App()
app.add_page(index)
