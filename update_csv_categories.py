#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

files_to_update = [
    "/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA_updated.csv",
    "/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA.csv",
    "/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/ZESTAWY PLAKATÓW.csv"
]

# Replacements to make
replacements = {
    "Grafiki i Plakaty": "Obrazy i plakaty chrześcijańskie",
    "Najchętniej kupowane grafiki": "Najchętniej kupowane obrazy i plakaty"
}

print("=" * 70)
print("CSV Categories and Tags Updater")
print("=" * 70)

for filepath in files_to_update:
    if os.path.exists(filepath):
        print(f"\n📁 Processing: {os.path.basename(filepath)}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old_text, new_text in replacements.items():
            count = content.count(old_text)
            if count > 0:
                print(f"   • Replacing '{old_text}' → '{new_text}': {count} occurrences")
                content = content.replace(old_text, new_text)
        
        # Write back
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Successfully updated!")
        else:
            print(f"   ℹ️  No changes needed.")
    else:
        print(f"\n❌ File not found: {filepath}")

print("\n" + "=" * 70)
print("✨ All files processed!")
print("=" * 70)
