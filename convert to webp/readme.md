# Image to WebP Converter

This script provides two utilities for converting images to the WebP format, optimized for web use. Each script serves a different purpose.

## Scripts Overview

1.  **`converter.py` (Bulk Conversion)**
    *   **Purpose**: Converts *all* images (`.jpg`, `.jpeg`, `.png`) from an input directory and its subdirectories.
    *   **Use Case**: Ideal for processing entire collections of images in one go.

2.  **`converter_clean.py` (Selective Conversion)**
    *   **Purpose**: Converts only a specific list of images defined in a CSV file (`output.csv`).
    *   **Use Case**: Perfect for when you only need to process a subset of images linked in a product catalog or database export.

## Requirements

### 1. ImageMagick

This script depends on the ImageMagick software suite. You must install it on your system before running the script.

**macOS (using [Homebrew](https://brew.sh/))**
```bash
brew install imagemagick
```

**Windows**
Download and run the latest installer from the [official ImageMagick website](https://imagemagick.org/script/download.php). Make sure to check the box **"Install legacy utilities (e.g., convert)"** during the installation process.

### 2. Python 3

Ensure you have Python 3.8 or newer installed on your system.

## Installation

1.  Clone this repository or download the script files.
2.  Navigate to the project directory in your terminal.
3.  Install the required Python libraries using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Quick Start

**Important:** Before running either script, you need to set up the ImageMagick environment variables (especially on macOS with Homebrew):

```bash
export MAGICK_HOME=/opt/homebrew
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
```

### `converter.py` (Bulk Conversion)

Run the script from your terminal, providing the path to the input directory and the desired output directory. This script finds and converts every image in the source folder.

**Complete Command:**
```bash
export MAGICK_HOME=/opt/homebrew && export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH && python converter.py <input_directory> <output_directory>
```

**Example:**
```bash
export MAGICK_HOME=/opt/homebrew && export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH && python converter.py ./source_images ./converted_images
```

### `converter_clean.py` (Selective Conversion)

This script reads image filenames from the `Images` column in `output.csv`, finds them in the input directory, and converts only those specific files.

**Prerequisites:**
*   A file named `output.csv` must be present in the same directory as the script.
*   The CSV must contain a column named `Images` with URLs to the images. The script extracts filenames from these URLs.

**Complete Command:**
```bash
export MAGICK_HOME=/opt/homebrew && export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH && python converter_clean.py <input_directory> <output_directory>
```

**Example:**
```bash
export MAGICK_HOME=/opt/homebrew && export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH && python converter_clean.py ./source_images ./converted_images_selective
```

## How It Works

- The script will start processing the designated images.
- A progress bar will show the status of the conversion.
- If any image cannot be compressed below 125kb even at the lowest quality setting, it will be saved in its smallest possible WebP version, and a note will be added to `log.txt` in the output directory.
- `converter_clean.py` will also log a list of any files that were specified in the CSV but could not be found in the input directory.

## Troubleshooting

### macOS: `ImportError: MagickWand shared library not found`

This is a common issue on macOS where the Python `wand` library cannot find the `ImageMagick` installation managed by Homebrew.

**Solution:** You need to set both `MAGICK_HOME` and `DYLD_LIBRARY_PATH` environment variables.

1.  **For the current terminal session:**
    Run the following commands before executing the script:
    ```bash
    export MAGICK_HOME=/opt/homebrew
    export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
    ```

2.  **For a permanent solution:**
    Add the commands to your shell's startup file (e.g., `.zshrc` for zsh):
    ```bash
    echo 'export MAGICK_HOME=/opt/homebrew' >> ~/.zshrc
    echo 'export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH' >> ~/.zshrc
    ```
    Then, restart your terminal or run `source ~/.zshrc`.

3.  **Quick fix for immediate use:**
    Use the complete command format shown in the Usage section above, which includes the environment variables in the same line.
