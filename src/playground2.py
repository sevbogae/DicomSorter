import numpy as np
import pydicom
import os
from pathlib import Path


def load_dicom_series(folder: str) -> tuple[np.ndarray, list[pydicom.Dataset]]:
    """
    Loads a DICOM series from a folder, sorted by SliceLocation.

    Args:
        folder: Path to the folder containing the DICOM series.
    Returns:
        Tuple of (volume, slices) where volume is a 3D numpy array (z, y, x)
        and slices is the list of sorted pydicom datasets.
    """
    slices = []
    for f in Path(folder).iterdir():
        try:
            ds = pydicom.dcmread(str(f))
            if hasattr(ds, "SliceLocation"):
                slices.append(ds)
        except Exception:
            continue

    slices.sort(key=lambda s: float(s.SliceLocation))
    volume = np.stack([s.pixel_array for s in slices], axis=0).astype(np.float32)
    return volume, slices


def apply_rescale(volume: np.ndarray, ds: pydicom.Dataset) -> np.ndarray:
    """
    Applies RescaleSlope and RescaleIntercept to convert to HU.

    Args:
        volume: Raw pixel array.
        ds:     Pydicom dataset to read rescale parameters from.
    Returns:
        Volume in Hounsfield Units.
    """
    slope     = float(getattr(ds, "RescaleSlope",     1))
    intercept = float(getattr(ds, "RescaleIntercept", 0))
    return volume * slope + intercept


def get_voxel_spacing(slices: list[pydicom.Dataset]) -> tuple[float, float, float]:
    """
    Returns voxel spacing as (slice_thickness, row_spacing, col_spacing) in mm.

    Args:
        slices: Sorted list of pydicom datasets.
    Returns:
        Tuple of (dz, dy, dx) in mm.
    """
    pixel_spacing = slices[0].PixelSpacing
    dy = float(pixel_spacing[0])
    dx = float(pixel_spacing[1])

    if len(slices) > 1:
        dz = abs(float(slices[1].SliceLocation) - float(slices[0].SliceLocation))
    else:
        dz = float(getattr(slices[0], "SliceThickness", 1.0))

    return dz, dy, dx


def reformat(
    volume: np.ndarray,
    spacing: tuple[float, float, float],
    plane: str
) -> tuple[np.ndarray, tuple[float, float]]:
    """
    Reformats a 3D volume into a coronal or sagittal stack.
    Resamples along the slice axis to correct for anisotropic voxel spacing.

    Args:
        volume:  3D numpy array (z, y, x) in HU.
        spacing: Voxel spacing (dz, dy, dx) in mm.
        plane:   Either 'coronal' or 'sagittal'.
    Returns:
        Tuple of (reformatted stack, (pixel_spacing_row, pixel_spacing_col)) in mm.
    """
    dz, dy, dx = spacing

    if plane == "coronal":
        # Slice along y-axis: result shape (y, z, x)
        stack = np.transpose(volume, (1, 0, 2))
        out_spacing = (dz, dx)
    elif plane == "sagittal":
        # Slice along x-axis: result shape (x, z, y)
        stack = np.transpose(volume, (2, 0, 1))
        out_spacing = (dz, dy)
    else:
        raise ValueError(f"Unknown plane '{plane}'. Use 'coronal' or 'sagittal'.")

    # Resample to isotropic spacing using zoom
    from scipy.ndimage import zoom
    zoom_z = dz / out_spacing[1]  # resample slice axis to match in-plane spacing
    stack = zoom(stack, (1, zoom_z, 1), order=1)

    return stack, out_spacing


def save_as_png(stack: np.ndarray, output_folder: str, ww: float = 400, wl: float = 40):
    """
    Saves each slice of the reformatted stack as a PNG with windowing applied.

    Args:
        stack:         Reformatted 3D array.
        output_folder: Folder to save PNG files to.
        ww:            Window width in HU.
        wl:            Window level (center) in HU.
    """
    from PIL import Image
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    lower = wl - ww / 2
    upper = wl + ww / 2

    for i, slc in enumerate(stack):
        slc_windowed = np.clip(slc, lower, upper)
        slc_norm = ((slc_windowed - lower) / (upper - lower) * 255).astype(np.uint8)
        img = Image.fromarray(slc_norm)
        img.save(os.path.join(output_folder, f"slice_{i:04d}.png"))


if __name__ == "__main__":
    DICOM_FOLDER  = r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-03-30\sorted_dicoms\QCCGent-Anderefantomen\Abdomen + C_RR\Abdomen +C 0,40 Br76 Q3 ax 0.4 120 sharp"
    OUTPUT_FOLDER = r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-03-30"
    PLANE         = "coronal"   # or "sagittal"
    WINDOW_WIDTH  = 400         # HU
    WINDOW_LEVEL  = 40          # HU (soft tissue)

    print("Loading DICOM series...")
    volume, slices = load_dicom_series(DICOM_FOLDER)
    volume = apply_rescale(volume, slices[0])

    print("Voxel spacing:", get_voxel_spacing(slices))
    spacing = get_voxel_spacing(slices)

    print(f"Reformatting to {PLANE} plane...")
    stack, out_spacing = reformat(volume, spacing, PLANE)

    print(f"Saving {len(stack)} slices to {OUTPUT_FOLDER}...")
    save_as_png(stack, OUTPUT_FOLDER, ww=WINDOW_WIDTH, wl=WINDOW_LEVEL)
    print("Done.")