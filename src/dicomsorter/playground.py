from pathlib import Path
import pydicom


def rename_leaf_folders_to_series_description(root_folder: Path) -> None:
    """Rename each leaf folder (directly containing DICOM files) to its SeriesDescription tag."""
    for dirpath in sorted(root_folder.rglob("*"), reverse=True):
        # Only process leaf directories (no subdirectories)
        if not dirpath.is_dir() or dirpath == root_folder:
            continue
        if any(child.is_dir() for child in dirpath.iterdir()):
            continue

        # Find the first DICOM file to read the SeriesDescription
        series_description = None
        for filepath in dirpath.iterdir():
            if not filepath.is_file():
                continue
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                series_description = ds.get("SeriesDescription", None)
                if series_description:
                    series_description = str(series_description).strip()
                    break
            except Exception:
                continue

        if not series_description:
            print(f"Skipping (no SeriesDescription found): {dirpath}")
            continue

        # Sanitize the series description for use as a folder name
        invalid_chars = r'\/:*?"<>|'
        for ch in invalid_chars:
            series_description = series_description.replace(ch, "_")

        new_path = dirpath.parent / series_description

        # Avoid collision if a folder with that name already exists
        if new_path.exists() and new_path != dirpath:
            counter = 1
            while (dirpath.parent / f"{series_description}_{counter}").exists():
                counter += 1
            new_path = dirpath.parent / f"{series_description}_{counter}"

        if new_path == dirpath:
            print(f"Already correctly named: {dirpath}")
            continue

        dirpath.rename(new_path)
        print(f"Renamed: {dirpath!r} -> {new_path!r}")


if __name__ == "__main__":
    root: Path = Path(r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-03-30\exported_weasis")
    rename_leaf_folders_to_series_description(root)
