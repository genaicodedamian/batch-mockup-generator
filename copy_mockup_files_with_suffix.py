#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do kopiowania plików mockup z dodaniem sufiksu 'n'
"""

import shutil
from pathlib import Path

# Ścieżka do folderu mockup
mockup_folder = Path("/Users/damianaugustyn/Documents/projects/Smart PS replacer/mockup")

# Lista plików do skopiowania (bez sufiksu 'n')
source_files = [
    "10.psd", "11.psd", "12.psd", "13.psd", "14.psd", "15.psd",
    "16.psd", "17.psd", "18.psd", "19.psd", "1.psd", "20.psd",
    "21.psd", "22.psd", "2.psd", "3.psd", "4.psd", "5.psd",
    "6.psd", "7.psd", "8.psd", "9.psd"
]

print("🔄 Kopiowanie plików z sufiksem 'n'...\n")

success_count = 0
error_count = 0

for source_file in source_files:
    source_path = mockup_folder / source_file
    
    # Tworzymy nową nazwę z sufiksem 'n'
    # Np. "10.psd" → "10n.psd"
    base_name = source_file.replace('.psd', '')
    dest_file = f"{base_name}n.psd"
    dest_path = mockup_folder / dest_file
    
    try:
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            print(f"✅ {source_file} → {dest_file}")
            success_count += 1
        else:
            print(f"❌ Plik źródłowy nie istnieje: {source_file}")
            error_count += 1
    except Exception as e:
        print(f"❌ Błąd podczas kopiowania {source_file}: {str(e)}")
        error_count += 1

print(f"\n📊 Podsumowanie:")
print(f"   ✅ Pomyślnie skopiowane: {success_count}")
print(f"   ❌ Błędy: {error_count}")

if error_count == 0:
    print(f"\n🎉 Wszystkie pliki zostały pomyślnie skopiowane!")
