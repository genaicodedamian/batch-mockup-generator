# Implementation Plan

This document outlines the steps to create a new script, `converter_clean.py`, based on `converter.py`. The new script will selectively convert images based on a list provided in a CSV file.

### Phase 1: Setup and Data Extraction from CSV

1.  **Create New Script**:
    *   Duplicate `converter.py` and save it as `converter_clean.py`.
2.  **Add Dependencies**:
    *   Add `pandas` to `requirements.txt` for efficient CSV processing.
3.  **Implement CSV Parsing Function (`extract_filenames_from_csv`)**:
    *   This function will be responsible for reading `output.csv`.
    *   It will target the `Images` column specifically.
    *   **URL Handling**:
        *   It will handle cells containing multiple URLs, separated by ", ".
        *   Empty cells will be ignored.
    *   **Filename Extraction**:
        *   For each URL, it will extract the filename from the end of the path.
        *   It will strip the `.webp` extension to get a base filename.
    *   **Unique List**: It will use a Python `set` to store the base filenames, automatically handling any duplicates.
    *   The function will return a set of unique base filenames required for conversion.

### Phase 2: File Discovery and User Confirmation

1.  **Implement Source File Search (`find_source_files`)**:
    *   This function will take the input directory and the set of target base filenames as arguments.
    *   It will recursively scan the input directory.
    *   **Matching Logic**:
        *   For each file found, it will check if its base name (case-sensitive) is in the target set.
        *   It will validate that the file has a permitted extension: `.png`, `.jpg`, or `.jpeg`.
    *   **Output**: The function will return two lists:
        *   A list of full paths to the image files that were found and are ready for conversion.
        *   A list of base filenames that were present in the CSV but could not be found in the input directory.
2.  **Implement Confirmation Step in `main`**:
    *   Call the functions from Phase 1 and Phase 2.
    *   Display a summary to the user:
        *   Number of files found and ready for conversion.
        *   A list of all missing files.
    *   Prompt the user for confirmation (e.g., "Continue? (y/n)") before starting the conversion process. If the user input is not 'y', the script will terminate.

### Phase 3: Integration with Conversion Logic

1.  **Modify `main` function in `converter_clean.py`**:
    *   The list of files to be processed will now come from `find_source_files` (Phase 2), not from a general directory scan (`input_path.rglob('*')`).
2.  **Logging**:
    *   The list of missing files will be logged to `log.txt` for later review. A dedicated function will be created for this.
3.  **File Handling**:
    *   The script will be configured to overwrite any existing files in the output directory to ensure the latest version is always present.

### Phase 4: Documentation

1.  **Update `readme.md`**:
    *   Create a new section detailing the functionality and usage of `converter_clean.py`.
    *   Clearly explain its dependency on `output.csv` and the `Images` column.
    *   Provide a clear command-line usage example.
    *   Refine the description for the original `converter.py` to clarify that it converts *all* images in the input folder, contrasting it with the new script's selective approach.
