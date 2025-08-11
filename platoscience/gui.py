import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import os

class ScraperGUI(tk.Tk):
    """
    A Tkinter-based GUI for controlling a Scrapy web scraper.

    This class creates a window that allows the user to select a US state,
    specify an output filename, and start a Scrapy crawl. It runs the
    Scrapy process in a separate thread to keep the GUI responsive.
    """
    def __init__(self):
        super().__init__()
        self.title("Webscraper Control Panel")
        self.geometry("400x230") # Increased height for the new field
        self.resizable(False, False)

        # A list of US states for the dropdown menu.
        self.us_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
            "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
            "New Hampshire", "New Jersey", "New Mexico", "New York",
            "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
            "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
            "West Virginia", "Wisconsin", "Wyoming"
        ]

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Widgets ---
        # State Selection
        state_label = ttk.Label(main_frame, text="State:")
        state_label.grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.state_var = tk.StringVar()
        self.state_combobox = ttk.Combobox(main_frame, textvariable=self.state_var, values=self.us_states, state="readonly")
        self.state_combobox.grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.state_combobox.set("California") # Default value

        # Search Term (as in the image, though not used by the current spider)
        #search_label = ttk.Label(main_frame, text="Search term:")
        #search_label.grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)
        #self.search_var = tk.StringVar()
        #self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var)
        #self.search_entry.grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        #self.search_entry.insert(0, "apartments") # Default value

        # Output Filename
        file_label = ttk.Label(main_frame, text="Output File:")
        file_label.grid(column=0, row=2, sticky=tk.W, padx=5, pady=5)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(main_frame, textvariable=self.file_var)
        self.file_entry.grid(column=1, row=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.file_entry.insert(0, "output.json") # Default value

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(column=0, row=3, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping_thread)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        exit_button = ttk.Button(button_frame, text="Exit", command=self.quit)
        exit_button.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure grid resizing
        main_frame.columnconfigure(1, weight=1)

    def start_scraping_thread(self):
        """
        Starts the scraping process in a new thread to prevent the GUI from freezing.
        """
        self.start_button.config(state=tk.DISABLED)
        self.scraping_thread = threading.Thread(target=self.run_scraper, daemon=True)
        self.scraping_thread.start()
        self.check_thread()

    def check_thread(self):
        """
        Checks if the scraping thread is still running. If it has finished,
        it re-enables the start button.
        """
        if self.scraping_thread.is_alive():
            self.after(100, self.check_thread)
        else:
            self.start_button.config(state=tk.NORMAL)

    def run_scraper(self):
        """
        This function runs in a separate thread. It executes the Scrapy spider
        using a subprocess.
        """
        selected_state = self.state_var.get()
        if not selected_state:
            messagebox.showerror("Error", "Please select a state.")
            return

        output_file = self.file_var.get().strip()
        if not output_file:
            # If the user leaves the filename blank, create a default one.
            output_file = f"{selected_state.lower().replace(' ', '_')}_providers.json"
        
        # Ensure the filename ends with .json
        if not output_file.lower().endswith('.json'):
            output_file += '.json'

        self.status_var.set(f"Status: Scraping {selected_state}...")
        
        command = [
            "scrapy", "crawl", "psychologytoday",
            "-s", f"STATES_TO_CRAWL=['{selected_state}']",
            "-o", output_file
        ]

        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(os.path.abspath(__file__)), shell=True)
            self.status_var.set(f"Status: Successfully scraped {selected_state}. Data saved to {output_file}")
            messagebox.showinfo("Success", f"Scraping for {selected_state} finished successfully!\nData saved to {output_file}")

        except subprocess.CalledProcessError as e:
            error_message = f"Error scraping {selected_state}.\n"
            error_message += f"Scrapy log:\n{e.stderr}"
            self.status_var.set(f"Status: Error scraping {selected_state}.")
            messagebox.showerror("Scraping Error", error_message)
        except FileNotFoundError:
            self.status_var.set("Status: Error - Scrapy command not found.")
            messagebox.showerror("Error", "Could not find the 'scrapy' command. Make sure Scrapy is installed and in your system's PATH.")
        except Exception as e:
            self.status_var.set(f"Status: An unexpected error occurred.")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
