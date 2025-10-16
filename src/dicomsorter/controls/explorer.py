import os, sys, subprocess
from pathlib import Path
import webbrowser


def open_folder(path: Path) -> None:
    """Open a folder in the system's file explorer.

    Parameters
    ----------
    path : Path
        The path to the folder to open.
    """
    if not path.is_dir():
        raise ValueError(f"The path {path} is not a valid directory.")

    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


def open_website(url: str) -> None:
    """Open a website in the default web browser.

    Parameters
    ----------
    url : str
        The URL of the website to open.
    """
    webbrowser.open(url)


def get_asset(relative_path: str) -> Path:
    """Get the absolute path to an asset file.

    Parameters
    ----------
    relative_path: str
        The relative path to the asset file.

    Returns
    -------
    str
        The absolute path to the asset file.
    """
    # Check if the application is run from a frozen state (e.g., an executable created with PyInstaller).
    # PyInstaller sets sys.frozen to True and uses sys._MEIPASS to store the temporary directory.
    if getattr(sys, "frozen", False):  # Returns False if the attribute 'frozen' does not exist.
        # We are running in a frozen state, i.e., from the executable. We need to use the temporary directory
        # created by PyInstaller: sys._MEIPASS.
        base: Path = Path(getattr(sys, "_MEIPASS"))  # Since there is no default value, we can use getattr safely.
    else:
        # We are not running in a frozen state, i.e., from the source code. Use the current directory.
        # __file__ is the path to the current file.
        # resolve() gives the absolute path.
        # parent.parent goes two levels up to the root of the project (one level would be the utils directory).
        base = Path(__file__).resolve().parent.parent

    return base / relative_path


if __name__ == "__main__":
    open_folder(Path.home())
