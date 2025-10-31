#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os

filepath = "/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/ZESTAWY PLAKATÓW.csv"

# Replacements to make in both SKU and Parent columns
replacements = {
    "172_173": "172+173",
    "98_99_100": "98+99+100",
    "54_55": "54+55"
}

print("=" * 70)
print("ZESTAWY PLAKATÓW.csv - Update SKU and Parent Columns")
print("=" * 70)

if not os.path.exists(filepath):
    print(f"\n❌ File not found: {filepath}")
    exit(1)

print(f"\n📁 Processing: {os.path.basename(filepath)}")

# Read CSV file
with open(filepath, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f"   • Total rows: {len(rows)}")
print(f"   • Columns: {len(fieldnames)}")

# Track changes
changes_by_column = {
    'SKU': {key: 0 for key in replacements},
    'Parent': {key: 0 for key in replacements}
}

# Process rows
for row in rows:
    # Update SKU column
    if 'SKU' in row and row['SKU']:
        for old_val, new_val in replacements.items():
            if old_val in row['SKU']:
                row['SKU'] = row['SKU'].replace(old_val, new_val)
                changes_by_column['SKU'][old_val] += 1
    
    # Update Parent column
    if 'Parent' in row and row['Parent']:
        for old_val, new_val in replacements.items():
            if old_val in row['Parent']:
                row['Parent'] = row['Parent'].replace(old_val, new_val)
                changes_by_column['Parent'][old_val] += 1

# Write back to CSV
with open(filepath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n✅ Changes completed:")

total_changes = 0
for column_name, replacements_dict in changes_by_column.items():
    print(f"\n   {column_name} column:")
    for old_val, count in replacements_dict.items():
        if count > 0:
            print(f"     • {old_val} → {replacements[old_val]}: {count} occurrences")
            total_changes += count

print(f"\n   📊 Total changes: {total_changes}")

print("\n" + "=" * 70)
print("✨ File successfully updated!")
print("=" * 70)
