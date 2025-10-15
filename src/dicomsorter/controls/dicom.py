from typing import Generator

import pydicom
from pathlib import Path


def find_dicoms_in_folder(folder: Path, allowed_extensions: set[str] = None) -> list[Path]:
    """Recursively find all DICOM files in a folder.

    Parameters
    ----------
    folder : Path
        The folder to search for DICOM files.
    allowed_extensions : set[str], optional
        A set of allowed file extensions. If None all files are returned, by default None.

    Returns
    -------
    list[Path]
        A list of Paths to the found DICOM files.
    """
    if allowed_extensions is None:
        return [p for p in folder.rglob('*') if p.is_file()]

    return [p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in allowed_extensions]


def read_dicom_file(dicom_path: Path) -> pydicom.Dataset:
    """Read a DICOM file and return the dataset.

    Parameters
    ----------
    dicom_path : Path
        The path to the DICOM file.

    Returns
    -------
    pydicom.Dataset
        The DICOM dataset.
    """
    return pydicom.dcmread(dicom_path, force=True)


def clean_text(text: str, forbidden_symbols: set[str] = None) -> str:
    """Clean and standardize text descriptions, which means replacing forbidden symbols with underscores and converting
    to lowercase.

    Parameters
    ----------
    text : str
        The text to clean.
    forbidden_symbols : set[str]
        A set of symbols to replace with underscores. If None, a default set is used:
        {"*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "}

    Returns
    -------
    str
        The cleaned text.
    """
    if forbidden_symbols is None:
        forbidden_symbols = {"*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "}

    # Create a translation table that maps each forbidden symbol to an underscore.
    table = {ord(c): '_' for c in forbidden_symbols}

    return str(text).translate(table).lower()


def create_path(dicom: pydicom.Dataset, destination_folder: Path, folder_structure: str = None,
                file_name_structure: str = None) -> Path:
    """Create the full path for saving the DICOM file based on its metadata.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset.
    destination_folder : Path
        The base destination folder where the DICOM file should be saved.
    folder_structure : str, optional
        A format string for the folder structure, by default
        "{PatientID}/{StudyDate}/{KVP}/{SliceThickness}/{ConvolutionKernel}".
    file_name_structure : str, optional
        A format string for the file name, by default
        "{Modality}_{InstanceNumber}_{KVP}_{SliceThickness}_{ConvolutionKernel}.dcm".

    Returns
    -------
    Path
        The full path where the DICOM file should be saved.
    """
    if folder_structure is None:
        folder_structure: str = "{PatientID}/{StudyDate}/{KVP}/{SliceThickness}/{ConvolutionKernel}"
    if file_name_structure is None:
        file_name_structure: str = "{Modality}_{InstanceNumber}_{KVP}_{SliceThickness}_{ConvolutionKernel}.dcm"

    tags: dict[str, str] = {
        "Modality": clean_text(dicom.get("Modality", "NA")),  # (0008,0060).
        "InstanceNumber": clean_text(dicom.get("InstanceNumber", "NA")),  # (0020,0013).
        "KVP": clean_text(dicom.get("KVP", "NA")),  # (0018,0060).
        "SliceThickness": clean_text(dicom.get("SliceThickness", "NA")),  # (0018,0050).
        "ConvolutionKernel": clean_text(dicom.get("ConvolutionKernel", "NA")),  # (0018,1210).
        "PatientID": clean_text(dicom.get("PatientID", "NA")),  # (0010,0020).
        "StudyDate": clean_text(dicom.get("StudyDate", "NA"))  # (0008,0020).
    }

    folder: str = folder_structure.format(**tags)
    file: str = file_name_structure.format(**tags)

    target: Path = destination_folder / folder / file

    return target


def save_dicom_file(dicom: pydicom.Dataset, file_path: Path) -> None:
    """Save the DICOM dataset to the specified file path.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset to save.
    file_path : Path
        The full path where the DICOM file should be saved.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)  # Parents will be created if necessary.
    dicom.save_as(file_path, write_like_original=False)  # Save as a standard DICOM file.


def sort_dicoms(source_path: Path, destination_path: Path, folder_structure: list[str] = None
                ) -> Generator[tuple[int, int]]:
    """Sort DICOM files from the source folder to the destination folder based on their metadata.

    Parameters
    ----------
    source_path : Path
        The source folder containing DICOM files.
    destination_path : Path
        The destination folder where sorted DICOM files will be saved.
    folder_structure : list[str], optional
        A list of DICOM tags to use for creating the folder structure. If None, a default structure is used,
        by default None.

    Yields
    ------
    Generator[tuple[int, int]]
        A generator yielding tuples of (current_index, total_files) for progress tracking.
    """
    dicom_files: list[Path] = find_dicoms_in_folder(folder=source_path)

    if not dicom_files:
        yield 0, 0
        return

    total: int = len(dicom_files)
    for i, dicom_file in enumerate(dicom_files):
        ds = read_dicom_file(dicom_path=dicom_file)
        file_path = create_path(dicom=ds, destination_folder=destination_path, folder_structure=folder_structure)
        save_dicom_file(dicom=ds, file_path=file_path)
        yield i, total


if __name__ == "__main__":
    source: Path = Path(r"C:\Users\sevbogae\programs\python\DicomSorter\GE_A")
    destination: Path = Path(r"C:\Users\sevbogae\programs\python\DicomSorter\sorted")
    sort_dicoms(source, destination)
