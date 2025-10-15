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


if __name__ == "__main__":
    open_folder(Path.home())
