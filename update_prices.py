import csv
import os
from decimal import Decimal

def process_csv_file(file_path):
    """
    For each row:
    1. Copy 'Sale price' value to 'Regular price'
    2. Clear the 'Sale price' (set to empty)
    3. Add 4.06504065 to the new 'Regular price' value
    """
    # Read the CSV file
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Process each row
    modified_count = 0
    for row in rows:
        sale_price = row.get('Sale price', '').strip()
        
        # Only process if Sale price has a value
        if sale_price:
            try:
                # Convert to Decimal for precise arithmetic
                sale_price_decimal = Decimal(sale_price)
                addition = Decimal('4.06504065')
                new_regular_price = sale_price_decimal + addition
                
                # Update the row
                row['Regular price'] = str(new_regular_price)
                row['Sale price'] = ''
                modified_count += 1
            except:
                print(f"  Warning: Could not process Sale price '{sale_price}' in row {row.get('Name', 'Unknown')}")
    
    # Write back to the same file
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    
    return modified_count

# Process all three files
files_to_process = [
    '/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA.csv',
    '/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA_updated.csv',
    '/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/ZESTAWY PLAKATÓW.csv'
]

print("Processing files...\n")
for file_path in files_to_process:
    file_name = file_path.split('/')[-1]
    if os.path.exists(file_path):
        print(f"Processing: {file_name}")
        count = process_csv_file(file_path)
        print(f"  ✓ Updated {count} rows\n")
    else:
        print(f"  ✗ File not found: {file_path}\n")

print("Done!")
