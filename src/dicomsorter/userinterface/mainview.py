import tkinter as tk
from pathlib import Path
from tkinter import ttk
from tkinter import messagebox, filedialog

from dicomsorter.controls.dicom import sort_dicoms
from dicomsorter.controls.explorer import open_folder, open_website


class MainView:

    def __init__(self) -> None:
        self._root: tk.Tk = tk.Tk()

        self._size: tuple[int, int] = (800, 260)
        self._position: tuple[int, int] = (0, 0)
        self._title: str = "DICOM Sorter"
        self._version: tuple[int, int] = (1, 0)
        self._author: str = "Seppe Van Bogaert"
        self._year: str = "2025"

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Initialize the main window.
        self._root.title(string=self._title)
        self._root.geometry(newGeometry=f"{self._size[0]}x{self._size[1]}"
                                        f"+{(self._root.winfo_screenwidth() - self._size[0]) // 2 + self._position[0]}"
                                        f"+{(self._root.winfo_screenheight() - self._size[1]) // 2 + self._position[1]}")
        self._root.minsize(width=500, height=260)

        # Creating the menubar.
        menubar: tk.Menu = tk.Menu(master=self._root)

        # Adding the File menu.
        file_menu: tk.Menu = tk.Menu(master=menubar, tearoff=False)
        file_menu.add_command(label="Exit", command=self._root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Adding the Help menu.
        help_menu: tk.Menu = tk.Menu(master=menubar, tearoff=False)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)
        help_menu.add_command(label="DICOM Tags", command=lambda: open_website("https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html"))
        menubar.add_cascade(label="Help", menu=help_menu)

        # Attach the menubar to the window.
        self._root.config(menu=menubar)

        # Add a label, input field, and button to the main window for the source and destination folders.
        paths_frame: ttk.Frame = ttk.Frame(master=self._root, padding="10")
        paths_frame.pack(fill="x")
        paths_frame.columnconfigure(index=1, weight=1)

        ttk.Label(master=paths_frame, text="Source Folder:").grid(row=0, column=0, padx=(0, 10), sticky="e")
        ttk.Label(master=paths_frame, text="Destination Folder:").grid(row=1, column=0, padx=(0, 10), sticky="e")

        self._source_entry: ttk.Entry = ttk.Entry(master=paths_frame)
        self._source_entry.grid(row=0, column=1, sticky="ew", rowspan=True, padx=(0, 10))
        self._source_entry.bind(sequence="<FocusOut>", func=lambda event: self._copy_source_to_destination())
        self._destination_entry: ttk.Entry = ttk.Entry(master=paths_frame)
        self._destination_entry.grid(row=1, column=1, sticky="ew", rowspan=True, padx=(0, 10))

        ttk.Button(master=paths_frame, text="Browse...",
                   command=lambda: self._browse_button_pressed(kind="source")
                   ).grid(row=0, column=2, padx=(0, 10), sticky="w")
        ttk.Button(master=paths_frame, text="Browse...",
                   command=lambda: self._browse_button_pressed(kind="destination")
                   ).grid(row=1, column=2, padx=(0, 10), sticky="w")

        # Add a label, input field, and button to the main window for the file and folder structure.
        structure_frame: ttk.Frame = ttk.Frame(master=self._root, padding="10")
        structure_frame.pack(fill="x")
        structure_frame.columnconfigure(index=1, weight=1)

        ttk.Label(master=structure_frame, text="File name structure:").grid(row=0, column=0, padx=(0, 10), sticky="e")
        ttk.Label(master=structure_frame, text="Folder name structure:").grid(row=1, column=0, padx=(0, 10), sticky="e")

        self._default_file_structure = tk.StringVar(
            value="{Modality}_{InstanceNumber}_{KVP}_{SliceThickness}_{ConvolutionKernel}.dcm"
        )
        self._default_folder_structure = tk.StringVar(
            value="{PatientID}/{StudyDate}/{KVP}/{SliceThickness}/{ConvolutionKernel}"
        )
        self._file_structure_entry: ttk.Entry = ttk.Entry(master=structure_frame,
                                                          textvariable=self._default_file_structure)
        self._file_structure_entry.grid(row=0, column=1, sticky="ew", rowspan=True, padx=(0, 10))
        self._folder_structure_entry: ttk.Entry = ttk.Entry(master=structure_frame,
                                                            textvariable=self._default_folder_structure)
        self._folder_structure_entry.grid(row=1, column=1, sticky="ew", rowspan=True, padx=(0, 10))

        ttk.Button(master=structure_frame, text="Default",
                   command=lambda: self._default_button_pressed(kind="file")
                   ).grid(row=0, column=2, padx=(0, 10), sticky="w")
        ttk.Button(master=structure_frame, text="Default",
                   command=lambda: self._default_button_pressed(kind="folder")
                   ).grid(row=1, column=2, padx=(0, 10), sticky="w")

        # Add a button to start the sorting process.
        ttk.Button(self._root, text="Start Sorting", command=self._start_sorting_button_pressed).pack(pady=20)
        self._root.bind(sequence="<Return>", func=lambda event: self._start_sorting_button_pressed())

    def _copy_source_to_destination(self) -> None:
        """Copy the source folder path to the destination folder path, with minor changes."""
        entry_dest: str = self._source_entry.get()

        if not entry_dest:
            return  # Do nothing if the source entry is empty.

        parent_folder: Path = Path(entry_dest).parent
        self._destination_entry.delete(first=0, last=tk.END)
        self._destination_entry.insert(index=0,
                                       string=str(parent_folder / "sorted_dicoms").replace("\\", "/"))

    def _default_button_pressed(self, kind: str) -> None:
        """Set the default structure in the appropriate entry field.

        Parameters
        ----------
        kind : str
            The kind of structure to set ('file' or 'folder').
        """
        if kind not in ("file", "folder"):
            raise ValueError("Invalid kind. Must be 'file' or 'folder'.")

        # Put the default in the appropriate entry field.
        entry: tk.Entry = self._file_structure_entry if kind == "file" else self._folder_structure_entry
        entry.delete(first=0, last=tk.END)
        entry.insert(index=0,
                     string={"file": "{Modality}_{InstanceNumber}_{KVP}_{SliceThickness}_{ConvolutionKernel}.dcm",
                             "folder": "{PatientID}/{StudyDate}/{KVP}/{SliceThickness}/{ConvolutionKernel}"}[kind]
                     )

    def _start_sorting_button_pressed(self) -> None:
        """Handle the event when the start sorting button is pressed."""
        source_folder: str = self._source_entry.get()
        destination_folder: str = self._destination_entry.get()

        if not source_folder or not destination_folder:
            messagebox.showwarning(title="Input Required",
                                   message="Please specify both a source and a destination folder.")
            return

        # Create a progress bar.
        self._progress_bar = ttk.Progressbar(master=self._root, mode="determinate")
        self._progress_bar.pack(fill="x", padx=10, pady=10)
        self._progress_bar["value"] = 0

        self._progress_iteration = sort_dicoms(source_path=Path(source_folder),
                                               destination_path=Path(destination_folder))
        self._update_progress_bar()

    def _update_progress_bar(self) -> None:
        try:
            iteration, total = next(self._progress_iteration)
            if total > 0:
                self._progress_bar["maximum"] = total
                self._progress_bar["value"] = iteration  # 'iteration' is a one-based index.
            # Schedule next update.
            self._root.after_idle(func=self._update_progress_bar)  # type: ignore
        except StopIteration:
            self._progress_bar.destroy()
            self._show_done_message()

    def _show_done_message(self) -> None:
        """Show a dialog indicating that the sorting is done, with an option to open the destination folder."""
        window = tk.Toplevel(master=self._root)
        window.title("Sorting Complete")
        window.geometry(
            f"200x75+{(self._root.winfo_screenwidth() - 200) // 2}+{(self._root.winfo_screenheight() - 75) // 2}"
        )
        window.resizable(width=False, height=False)
        ttk.Label(master=window, text="DICOM sorting is complete.").pack(anchor="w", padx=10, pady=10)

        # Button frame.
        button_frame = ttk.Frame(master=window)
        button_frame.pack(pady=(0, 10))

        ttk.Button(master=button_frame, text="Open Folder",
                   command=lambda: open_folder(Path(self._destination_entry.get()))
                   ).pack(side="left", padx=5)
        ttk.Button(master=button_frame, text="Ok", command=window.destroy).pack(side="left", padx=5)

        window.transient(master=self._root)  # Set to be on top of the main window.
        window.grab_set()  # Make the dialog modal, i.e., block interaction with other windows.
        self._root.wait_window(window)  # Wait until the window is closed.

    def _browse_button_pressed(self, kind: str) -> None:
        """Handle the event when the browse button is pressed.

        Parameters
        ----------
        kind : str
            The kind of folder to browse for ('source' or 'destination').
        """
        if kind not in ("source", "destination"):
            raise ValueError("Invalid kind. Must be 'source' or 'destination'.")

        # let the user choose a folder.
        folder_selected: str = filedialog.askdirectory(title=f"Select {kind.title()} Folder")

        # Do nothing if the user canceled the dialog.
        if not folder_selected:
            return  # User canceled the dialog.

        # Add the folder to the appropriate entry field.
        entry: tk.Entry = self._source_entry if kind == "source" else self._destination_entry
        entry.delete(first=0, last=tk.END)
        entry.insert(index=0, string=folder_selected)

        if kind == "source":
            self._copy_source_to_destination()

    def _show_about(self) -> None:
        """Show the dialog 'About'."""
        messagebox.showinfo(title="About",
                            message=f"{self._title}\n"
                                    f"Seppe Van Bogaert\n"
                                    f"Universiteit Gent\n"
                                    f"Version {'.'.join([str(i) for i in self._version])}")

    @staticmethod
    def _show_help() -> None:
        """Show the dialog 'Help'."""
        messagebox.showinfo(title="Help",
                            message=f"This is a simple DICOM sorter application.\n\n"
                                    f"It sorts DICOM files inside a single folder into a folder structure, based on the DICOM tags.\n\n"
                                    f"Inside the 'Source Folder', select the folder containing the unsorted DICOM files. You can use the 'Browse...' button to navigate using the file explorer. The 'Destination Folder' is where the sorted DICOM files will be saved. This folder will be created if it does not exist. You can also use the 'Browse...' button here.\n\n"
                                    f"The 'File name structure' and 'Folder name structure' fields allow you to control how the sorting is done. You can use DICOM tags enclosed in curly braces {{}} to define the structure. The 'File name structure' defines how the files will be named, while the 'Folder name structure' defines how the files will be organized into folders. You can use the 'Default' buttons to reset the structures to their default values.\n\n"
                                    f"You can find a list of supported DICOM tags by navigating to 'Help' > 'DICOM Tags'. Use the Keyword column.\n\n"
                                    f"If you end up in trouble, please report the issue."
                            )

    def run(self) -> None:
        self._root.mainloop()


if __name__ == "__main__":
    app = MainView()
    app.run()
