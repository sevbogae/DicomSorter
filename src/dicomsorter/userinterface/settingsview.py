import tkinter as tk
from tkinter import ttk
from typing import Any

from dicomsorter.controls.settings import read_settings, save_settings


class SettingsView:

    def __init__(self, master: tk.Tk) -> None:
        self._master = master
        self._window = tk.Toplevel(master)

        self._settings: dict[str, Any] = read_settings()
        self._create_notebook()

    @property
    def window(self) -> tk.Toplevel:
        return self._window

    def _create_notebook(self) -> None:
        # Some window settings.
        self._window.title("Settings")
        self._window.transient(self._master)
        self._window.grab_set()  # Make the settings window modal.
        self._window.focus_force()  # Focus on the settings window.

        # Position the window in the center of the parent window.
        x = self._master.winfo_x() + (self._master.winfo_width() // 2) - (self._window.winfo_reqwidth() // 2)
        y = self._master.winfo_y() + (self._master.winfo_height() // 2) - (self._window.winfo_reqheight() // 2)
        self._window.geometry(newGeometry=f"700x200+{max(0, x)}+{max(0, y)}")
        self._window.minsize(width=600, height=200)

        # Add a notebook to hold different settings categories.
        self._notebook = ttk.Notebook(master=self._window)
        self._notebook.pack(fill="both", expand=True)

        # General settings tab.
        self._general_frame = ttk.Frame(master=self._notebook)
        self._notebook.add(child=self._general_frame, text="General")
        self._create_general_settings(master=self._general_frame)

        # When the window is closed, save the settings.
        self._window.protocol(name="WM_DELETE_WINDOW", func=self._on_close)

    def _create_general_settings(self, master: ttk.Frame) -> None:
        # Add a checkbox for enabling or disabling the common dicom tags buttons.
        tags_button_frame = ttk.LabelFrame(master=master, text="DICOM Tags Hints")
        tags_button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(master=tags_button_frame, text="Show buttons for common DICOM tags:").grid(column=0, row=0)
        self._common_tags_var = tk.BooleanVar(value=self._settings.get("enable_common_tags_buttons", False))
        self._common_tags_checkbox = ttk.Checkbutton(
            master=tags_button_frame,
            text="",
            variable=self._common_tags_var,
            command=self._update_settings,
        )
        self._common_tags_checkbox.grid(column=1, row=0, padx=10, pady=5)

        # Add an entry field for file path default settings.
        default_structure_frame = ttk.LabelFrame(master=master, text="Default Structures")
        default_structure_frame.pack(fill="x", padx=10, pady=10)
        # Make the second column expand with the frame
        default_structure_frame.columnconfigure(index=0, weight=0)
        default_structure_frame.columnconfigure(index=1, weight=1)

        ttk.Label(master=default_structure_frame, text="Default file structure:").grid(column=0, row=0, sticky="w")
        self._file_structure_var = tk.StringVar(value=self._settings.get("default_file_structure", ""))
        self._file_structure_entry = ttk.Entry(master=default_structure_frame, textvariable=self._file_structure_var, width=100)
        self._file_structure_entry.grid(column=1, row=0, padx=10, pady=5, sticky="ew")

        # Add an entry field for folder path default settings.
        ttk.Label(master=default_structure_frame, text="Default folder structure:").grid(column=0, row=1, sticky="w")
        self._output_folder_var = tk.StringVar(value=self._settings.get("default_folder_structure", ""))
        self._output_folder_entry = ttk.Entry(master=default_structure_frame, textvariable=self._output_folder_var, width=100)
        self._output_folder_entry.grid(column=1, row=1, padx=10, pady=5, sticky="ew")

    def _update_settings(self) -> None:
        """Update the settings dictionary with current values."""
        self._settings.update({"enable_common_tags_buttons": self._common_tags_var.get(),
                               "default_file_structure": self._file_structure_var.get(),
                               "default_folder_structure": self._output_folder_var.get()
                               })
        save_settings(self._settings)

    def _on_close(self) -> None:
        """Handle the window close event."""
        self._update_settings()
        self._window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    settings_view = SettingsView(master=root)
    root.mainloop()
