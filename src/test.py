# Alex Weston
# Digital Innovation Lab, Mayo Clinic

import os
import pydicom # pydicom is using the gdcm package for decompression

def clean_text(string):
    # clean and standardize text descriptions, which makes searching files easier
    forbidden_symbols = ["*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "]
    for symbol in forbidden_symbols:
        string = string.replace(symbol, "_") # replace everything with an underscore
    return string.lower()

# user specified parameters ----- HIER ABSOLUUT PAD INVULLEN, vergeet de dubbele slashes niet
src = r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-02-16_CT\QCCIQ\UNKNOWN\13394"
dst = r"C:\Users\sevbogae\OneDrive - UGent\Documents\QCC\2026\2026-02-16_CT"

print('reading file list...')
unsortedList = []
for root, dirs, files in os.walk(src):
    for file in files:
        #if ".dcm" in file:# exclude non-dicoms, good for messy folders
            unsortedList.append(os.path.join(root, file))

print('%s files found.' % len(unsortedList))

for dicom_loc in unsortedList:
    # read the file
    ds = pydicom.dcmread(dicom_loc, force=True)

    # get patient, study, and series information
    patientID = clean_text(ds.get("PatientID", "NA"))
    studyDate = clean_text(ds.get("StudyDate", "NA"))
    studyDescription = clean_text(ds.get("StudyDescription", "NA"))
    seriesDescription = clean_text(ds.get("SeriesDescription", "NA"))
    sliceThickness = ds.get("SliceThickness", "NA")
    convKernel = ds.get("ConvolutionKernel", "NA")
    KVP = ds.get("KVP","NA")

    # generate new, standardized file name
    modality = ds.get("Modality","NA")
    studyInstanceUID = ds.get("StudyInstanceUID","NA")
    seriesInstanceUID = ds.get("SeriesInstanceUID","NA")
    instanceNumber = str(ds.get("InstanceNumber","0"))
    fileName = modality + "." + instanceNumber + str(KVP) + "_" + str(sliceThickness) + "_" + convKernel + ".dcm"

    # uncompress files (using the gdcm package)
    try:
        ds.decompress()
    except:
        print('an instance in file %s - %s - %s - %s" could not be decompressed. exiting.' % (patientID, studyDate, studyDescription, seriesDescription ))

    # save files to a 4-tier nested folder structure
    if not os.path.exists(os.path.join(dst, patientID)):
        os.makedirs(os.path.join(dst, patientID))

    if not os.path.exists(os.path.join(dst, patientID, studyDate, str(KVP))):
        os.makedirs(os.path.join(dst, patientID, studyDate, str(KVP)))

    if not os.path.exists(os.path.join(dst, patientID, studyDate, str(KVP), str(sliceThickness))):
        os.makedirs(os.path.join(dst, patientID, studyDate, str(KVP), str(sliceThickness)))

    if not os.path.exists(os.path.join(dst, patientID, studyDate, str(KVP), str(sliceThickness), convKernel)):
        os.makedirs(os.path.join(dst, patientID, studyDate, str(KVP), str(sliceThickness), convKernel))
        print('Saving out file: %s - %s - %s - %s.' % (patientID, str(KVP), str(sliceThickness), convKernel))

    ds.save_as(os.path.join(dst, patientID, studyDate, str(KVP), str(sliceThickness), convKernel, fileName))

print('done.')