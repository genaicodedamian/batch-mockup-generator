import argparse
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from threading import Lock
import pandas as pd

from wand.image import Image
from tqdm import tqdm

TARGET_SIZE_KB = 125
MAX_ITERATIONS = 14
LOG_LOCK = Lock()

def write_log(output_dir, source_path, final_size, final_quality):
    """Appends a message to the log file in a thread-safe manner."""
    with LOG_LOCK:
        log_file_path = os.path.join(output_dir, "log.txt")
        with open(log_file_path, "a") as f:
            final_size_kb = round(final_size / 1024, 2)
            f.write(
                f"File '{source_path}' could not be compressed to {TARGET_SIZE_KB}kb. "
                f"Saved with size: {final_size_kb}kb at quality: {final_quality}.\n"
            )

def log_missing_files(output_dir, missing_files):
    """Logs the list of missing files to the log file."""
    with LOG_LOCK:
        log_file_path = os.path.join(output_dir, "log.txt")
        with open(log_file_path, "a") as f:
            f.write("\n--- Missing Files ---\n")
            for filename in missing_files:
                f.write(f"{filename}\n")
            f.write("-- End Missing Files ---\n")

def extract_filenames_from_csv(csv_path, column_name="Images"):
    """
    Reads a CSV file and extracts a unique set of base filenames from image URLs
    in the specified column.
    """
    try:
        df = pd.read_csv(csv_path)
        if column_name not in df.columns:
            print(f"Error: Column '{column_name}' not found in {csv_path}")
            return set()

        filenames = set()
        for _, row in df.iterrows():
            cell_value = row[column_name]
            if not isinstance(cell_value, str):
                continue

            urls = [url.strip() for url in cell_value.split(',')]
            for url in urls:
                if url:
                    # Get the part after the last slash
                    filename_with_ext = url.split('/')[-1]
                    # Remove the .webp extension to get the base name
                    base_name = filename_with_ext.replace('.webp', '')
                    filenames.add(base_name)
        return filenames
    except FileNotFoundError:
        print(f"Error: The file {csv_path} was not found.")
        return set()
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return set()

def find_source_files(input_dir, target_basenames):
    """
    Scans the input directory to find actual image files that match the target base names.
    Returns a list of files to convert and a list of basenames that were not found.
    """
    files_to_convert = []
    found_basenames = set()
    
    all_files = list(Path(input_dir).rglob('*'))
    
    for p in all_files:
        if p.is_file() and p.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            base_name = p.stem
            if base_name in target_basenames:
                files_to_convert.append(str(p))
                found_basenames.add(base_name)

    missing_files = target_basenames - found_basenames
    return files_to_convert, list(missing_files)

def process_image(source_path_str, input_dir_str, output_dir_str):
    """
    Processes a single image: converts it to WebP, attempting to get it
    under TARGET_SIZE_KB.
    """
    source_path = Path(source_path_str)
    input_dir = Path(input_dir_str)
    output_dir = Path(output_dir_str)
    
    relative_path = source_path.relative_to(input_dir)
    output_path = output_dir / relative_path.with_suffix(".webp")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Image(filename=str(source_path)) as img:
            # 1. Try lossless compression first
            with img.clone() as cloned_img:
                cloned_img.format = 'webp'
                cloned_img.options['webp:lossless'] = 'true'
                blob = cloned_img.make_blob()
                if len(blob) <= TARGET_SIZE_KB * 1024:
                    output_path.write_bytes(blob)
                    return (str(source_path), "Success (Lossless)", round(len(blob) / 1024, 2))

            # 2. If lossless is too big, try iterative lossy compression
            best_quality = -1
            best_blob = None

            for i in range(MAX_ITERATIONS):
                quality = 95 - (i * 5)
                if quality <= 0: break
                
                with img.clone() as cloned_img:
                    cloned_img.format = 'webp'
                    cloned_img.compression_quality = quality
                    blob = cloned_img.make_blob()

                if best_blob is None or len(blob) < len(best_blob):
                    best_blob = blob
                    best_quality = quality

                if len(blob) <= TARGET_SIZE_KB * 1024:
                    output_path.write_bytes(blob)
                    return (str(source_path), f"Success (Q={quality})", round(len(blob) / 1024, 2))
            
            # 3. If still too big, save the smallest version found
            if best_blob:
                output_path.write_bytes(best_blob)
                final_size = len(best_blob)
                write_log(output_dir_str, source_path, final_size, best_quality)
                return (str(source_path), f"Warning ( oversize, Q={best_quality})", round(final_size / 1024, 2))

    except Exception as e:
        return (str(source_path), f"Error: {e}", -1)
    
    return (str(source_path), "Error: No suitable version found", -1)

def main():
    parser = argparse.ArgumentParser(description="Convert images to WebP with a target size based on a CSV file.")
    parser.add_argument("input_dir", help="Input directory containing images.")
    parser.add_argument("output_dir", help="Output directory to save converted images.")
    parser.add_argument("--csv_path", default="output.csv", help="Path to the CSV file.")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    if not input_path.is_dir():
        print(f"Error: Input directory not found at '{args.input_dir}'")
        return

    # Phase 1: Extract filenames from CSV
    target_basenames = extract_filenames_from_csv(args.csv_path)
    if not target_basenames:
        print("No filenames to process from CSV file.")
        return

    # Phase 2: Find source files and get user confirmation
    image_files, missing_files = find_source_files(args.input_dir, target_basenames)

    print(f"Found {len(image_files)} files to convert out of {len(target_basenames)} specified in the CSV.")
    if missing_files:
        print(f"Could not find {len(missing_files)} files:")
        for name in missing_files:
            print(f" - {name}")
    
    if not image_files:
        print("No matching image files found to convert.")
        if missing_files:
             log_missing_files(args.output_dir, missing_files)
        return

    proceed = input("Do you want to continue with the conversion? (y/n): ").lower()
    if proceed != 'y':
        print("Conversion cancelled by user.")
        return
        
    if missing_files:
        # Ensure output dir exists before logging
        output_path.mkdir(parents=True, exist_ok=True)
        log_missing_files(args.output_dir, missing_files)

    # Phase 3: Convert images
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(process_image, img_path, str(input_path), str(output_path))
            for img_path in image_files
        ]
        
        progress = tqdm(total=len(image_files), desc="Converting Images")
        for future in as_completed(futures):
            try:
                result = future.result()
                # You can optionally use the result for more detailed logging
                # print(f"Processed: {result[0]} -> {result[1]} ({result[2]} kb)")
            except Exception as e:
                print(f"A task generated an exception: {e}")
            progress.update(1)
        progress.close()

    print("\nConversion complete.")
    log_file = output_path / "log.txt"
    if log_file.exists():
        print(f"Some files could not be compressed to the target size or were missing. See '{log_file}' for details.")


if __name__ == "__main__":
    main()
