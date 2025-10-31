import csv
import os

def update_csv_categories(file_path):
    """
    Update Categories column for rows where Type='variable'
    by adding 'Grafiki i Plakaty, ' prefix to the beginning.
    """
    # Read the CSV file
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Update Categories for rows where Type='variable'
    modified_count = 0
    for row in rows:
        if row.get('Type') == 'variable':
            current_categories = row.get('Categories', '')
            # Only add prefix if it doesn't already start with "Grafiki i Plakaty, "
            if current_categories and not current_categories.startswith('Grafiki i Plakaty, '):
                row['Categories'] = 'Grafiki i Plakaty, ' + current_categories
                modified_count += 1
            elif not current_categories:
                # If Categories is empty, just add the prefix
                row['Categories'] = 'Grafiki i Plakaty, '
                modified_count += 1
    
    # Write back to the same file
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    
    return modified_count

# Process both files
files_to_process = [
    '/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA.csv',
    '/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA_updated.csv'
]

for file_path in files_to_process:
    if os.path.exists(file_path):
        print(f"Processing: {file_path}")
        count = update_csv_categories(file_path)
        print(f"  ✓ Updated {count} rows")
    else:
        print(f"  ✗ File not found: {file_path}")

print("\nDone!")
