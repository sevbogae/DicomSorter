import re
import shutil
import string
from typing import Generator, Optional, Callable

import pydicom
from pathlib import Path


# Default file name structure for instance naming. Users can override this.
DEFAULT_FILE_NAME_STRUCTURE: str = "{InstanceNumber}"


def is_dicom(path: Path) -> bool:
    """Check if a file is DICOM file by checking for the "DICM" magic word at byte offset 128. This is a common
    heuristic, but not foolproof, as some DICOM files may not have this signature, and some non-DICOM files might
    coincidentally have it. For a more robust check, you might want to attempt reading the file with pydicom and catch
    any exceptions that indicate it's not a valid DICOM file.

    Parameters
    ----------
    path : Path
        The path to the file to check.

    Returns
    -------
    bool
        True if the file is DICOM file, False otherwise.
    """
    try:
        with open(path, "rb") as f:
            f.seek(128)
            return f.read(4) == b"DICM"
    except OSError:
        return False


def find_dicoms_in_folder(folder: Path, function_check: Optional[Callable[[Path], bool]] = None) -> list[Path]:
    """Recursively find all DICOM files in a folder.

    Parameters
    ----------
    folder : Path
        The folder to search for DICOM files.
    function_check : Callable[[Path], bool], optional
        A function that takes a Path and returns True if it is a DICOM file. If None, the default is to check for the
        "DICM" magic word at byte offset 128.

    Returns
    -------
    list[Path]
        A list of Paths to the found DICOM files.
    """
    if function_check is None:
        function_check = is_dicom

    return [p for p in folder.rglob('*') if function_check(p)]


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
    return pydicom.dcmread(fp=dicom_path, force=True)


def clean_text(text: str, forbidden_symbols: set[str] = None) -> str:
    """Clean and standardize text for use in file and folder names.

    Replaces forbidden symbols with underscores, collapses consecutive underscores, strips
    leading/trailing underscores, and converts to lowercase.

    Parameters
    ----------
    text : str
        The text to clean.
    forbidden_symbols : set[str]
        A set of symbols to replace with underscores. If None, a default set is used covering
        characters forbidden on Windows ('?', '<', '>', '\\', '/', '|', ':', '*', '"') plus
        common punctuation and DICOM-specific separators ('^' in PersonName, '.', ',', etc.).

    Returns
    -------
    str
        The cleaned text, safe to use as a file or folder name component.
    """
    if forbidden_symbols is None:
        forbidden_symbols = {
            # Windows-forbidden path characters.
            '?', '<', '>', '\\', '/', '|', ':', '*', '"',
            # Common punctuation.
            '.', ',', '\'', '[', ']', ';', ' ',
            # DICOM PersonName component separator.
            '^',
        }

    table = {ord(c): '_' for c in forbidden_symbols}
    cleaned = str(text).translate(table).lower()
    cleaned = re.sub(r'_+', '_', cleaned)  # collapse consecutive underscores.
    return cleaned.strip('_')


def get_dicom_tag(dicom: pydicom.Dataset, key: str) -> str:
    """Look up and clean a single DICOM tag by keyword.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset.
    key : str
        The DICOM keyword, e.g. "PatientID" or "SeriesDescription". Any keyword
        recognized by pydicom is valid; unknown keywords return "NA".

    Returns
    -------
    str
        The cleaned tag value, or "NA" if the tag is absent.
    """
    return clean_text(dicom.get(key, "NA"))


def _resolve_structure(dicom: pydicom.Dataset, structure: str) -> str:
    """Resolve a format string by looking up the required DICOM tags dynamically.

    Parses all {Keyword} placeholders in structure, fetches each from the dataset
    via get_dicom_tag, and returns the formatted result. Any valid DICOM keyword
    can be used without pre-registration.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset.
    structure : str
        A format string with DICOM keyword placeholders, e.g.
        "{PatientID}/{StudyDate}_{StudyDescription}".

    Returns
    -------
    str
        The resolved string with all placeholders replaced by cleaned tag values.
    """
    keys = {fname for _, fname, _, _ in string.Formatter().parse(structure) if fname is not None}
    tags = {key: get_dicom_tag(dicom, key) for key in keys}
    return structure.format(**tags)


def create_sort_folder(dicom: pydicom.Dataset, destination_folder: Path) -> Path:
    """Create the sort folder path for a DICOM file based on its standard hierarchy.

    The folder name is fixed and not user-configurable:
        {SeriesInstanceUID}_Irradiation Event UID

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset.
    destination_folder : Path
        The root destination folder.

    Returns
    -------
    Path
        The folder where this DICOM file should be placed.
    """
    return destination_folder / _resolve_structure(dicom, "{SeriesInstanceUID}_{IrradiationEventUID}")


def create_file_name(dicom: pydicom.Dataset, used_names: set[str],
                     name_structure: str = None) -> str:
    """Create a unique file name for a DICOM instance within its destination folder.

    If the resolved name already exists in used_names, a numeric suffix (_1, _2, ...) is
    appended before the extension until a unique name is found.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset.
    used_names : set[str]
        The set of file names already used in the destination folder. Updated in-place with
        the returned name.
    name_structure : str, optional
        A format string using DICOM tag keywords, e.g. "{InstanceNumber}" or
        "{Modality}_{InstanceNumber}". The .dcm extension is always added automatically.
        Defaults to DEFAULT_FILE_NAME_STRUCTURE.

    Returns
    -------
    str
        A unique file name ending in .dcm.
    """
    if name_structure is None:
        name_structure = DEFAULT_FILE_NAME_STRUCTURE

    base = _resolve_structure(dicom, name_structure)

    candidate = f"{base}.dcm"
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    counter = 1
    while True:
        candidate = f"{base}_{counter}.dcm"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


def save_dicom_file(dicom: pydicom.Dataset, file_path: Path, *, decompress: bool = True) -> None:
    """Save the DICOM dataset to the specified file path.

    Parameters
    ----------
    dicom : pydicom.Dataset
        The DICOM dataset to save.
    file_path : Path
        The full path where the DICOM file should be saved.
    decompress : bool, optional
        Whether to attempt decompression if the DICOM dataset is compressed, by default True.
    """
    # Ensure the parent directory exists before saving the file. If it doesn't exist, it will be created.
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if the DICOM dataset is compressed by examining the Transfer Syntax UID in the file meta-information. If it
    # is compressed, attempt to decompress it using the pydicom library's built-in decompression functionality. If
    # decompression fails for any reason, catch the exception and print a warning message.
    if decompress and dicom.file_meta.TransferSyntaxUID.is_compressed:
        try:
            dicom.decompress()
        except Exception as e:
            print(f"Warning: Could not decompress DICOM file {file_path}. Error: {e}")

    try:
        dicom.save_as(file_path, write_like_original=False)
    except Exception as e:
        print(f"Error: Could not save DICOM file {file_path}. Error: {e}")


def sort_dicoms(source_path: Path, destination_path: Path,
                file_name_structure: str | None = None) -> Generator[tuple[int, int], None, None]:
    """Sort DICOM files from the source folder to the destination folder.

    The folder hierarchy is fixed (Patient → Study → Series) and always uses SeriesInstanceUID
    to guarantee that different reconstructions of the same acquisition are separated.
    Only the instance file name is user-configurable via file_name_structure.

    Parameters
    ----------
    source_path : Path
        The source folder containing DICOM files.
    destination_path : Path
        The destination folder where sorted DICOM files will be saved.
    file_name_structure : str, optional
        A format string for the instance file name, e.g. "{InstanceNumber}" or
        "{Modality}_{InstanceNumber}". If the resolved name collides within a folder,
        a numeric suffix (_1, _2, ...) is added automatically. Defaults to
        DEFAULT_FILE_NAME_STRUCTURE.

    Yields
    ------
    Generator[tuple[int, int]]
        Tuples of (current_index, total_files) for progress tracking. current_index is 1-based.
    """
    dicom_files: list[Path] = find_dicoms_in_folder(folder=source_path)

    if not dicom_files:
        yield 0, 0
        return

    # Track used file names per destination folder to detect and resolve naming collisions.
    # 'used_names_per_fodler' is a mapping of each destination folder to the set of file names already placed in it.
    used_names_per_folder: dict[Path, set[str]] = {}

    total: int = len(dicom_files)
    for i, dicom_file in enumerate(dicom_files, start=1):
        ds: pydicom.Dataset = read_dicom_file(dicom_path=dicom_file)

        folder: Path = create_sort_folder(dicom=ds, destination_folder=destination_path)

        if folder not in used_names_per_folder:
            used_names_per_folder[folder] = set()

        file_name: str = create_file_name(dicom=ds, used_names=used_names_per_folder[folder],
                                          name_structure=file_name_structure)
        save_dicom_file(dicom=ds, file_path=folder / file_name)
        yield i, total


def restructure_sorted_folders(root: Path, folder_structure: str,
                               file_name_structure: str | None = None) -> Generator[tuple[int, int], None, None]:
    """Rename the series subfolders (and optionally their files) inside a sorted destination.

    Reads one DICOM file per series subfolder to extract the metadata for the folder rename.
    If file_name_structure is provided, every file in each subfolder is also renamed before
    the folder is moved. File naming collisions within a folder are resolved automatically by
    appending _1, _2, etc.

    Parameters
    ----------
    root : Path
        The root destination folder produced by sort_dicoms, containing one flat subfolder
        per series.
    folder_structure : str
        A format string using DICOM tag keywords that defines the new folder hierarchy relative
        to root, e.g. "{PatientID}/{StudyDate}_{StudyDescription}/{SeriesNumber}_{SeriesDescription}".
    file_name_structure : str, optional
        A format string for the instance file name, e.g. "{InstanceNumber}" or
        "{Modality}_{InstanceNumber}". If None, existing file names are kept as-is.

    Yields
    ------
    Generator[tuple[int, int]]
        Tuples of (current_index, total_folders) for progress tracking. current_index is 1-based.
    """
    series_folders: list[Path] = [p for p in root.iterdir() if p.is_dir()]

    if not series_folders:
        yield 0, 0
        return

    total: int = len(series_folders)
    for i, series_folder in enumerate(series_folders, start=1):
        dicom_files: list[Path] = [p for p in series_folder.rglob('*') if p.is_file()]
        if not dicom_files:
            yield i, total
            continue

        # Read one file for the folder-level tags (all files in the folder share the same series).
        ds: pydicom.Dataset = read_dicom_file(dicom_path=dicom_files[0])

        if file_name_structure is not None:
            used_names: set[str] = set()
            for dicom_file in dicom_files:
                file_ds: pydicom.Dataset = read_dicom_file(dicom_path=dicom_file)
                new_name: str = create_file_name(dicom=file_ds, used_names=used_names,
                                                 name_structure=file_name_structure)
                dicom_file.rename(dicom_file.parent / new_name)

        new_path: Path = root / _resolve_structure(ds, folder_structure)
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(series_folder), str(new_path))
        yield i, total


if __name__ == "__main__":
    source: Path = Path(r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-05-20\beelden\GE_A")
    destination: Path = Path(r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-05-20\test")
    # for current, total in sort_dicoms(source, destination):
    #     print(f"{current}/{total}")

    for current, total in restructure_sorted_folders(destination, "{PatientID}/{StudyDate}/{KVP}/{SliceThickness}/{ConvolutionKernel}","{Modality}_{InstanceNumber}_{KVP}_{SliceThickness}_{ConvolutionKernel}.dcm"):
        print(f"{current}/{total}")
