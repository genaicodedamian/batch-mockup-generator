#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do sprawdzenia czy wszystkie pliki z config.json istnieją w odpowiednich folderach
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Ścieżki do folderów
project_folder = Path("/Users/damianaugustyn/Documents/projects/Smart PS replacer")
config_file = project_folder / "config.json"
input_folder = project_folder / "input"
mockup_folder = project_folder / "mockup"

def get_folder_files(folder_path):
    """Zwraca zbiór nazw plików w folderze (bez rozszerzeń dla porównania)"""
    files = set()
    if folder_path.exists():
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                files.add(file_path.name)
    return files

def load_config_mappings(config_path):
    """Ładuje mapowania z config.json"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    input_files = set()
    mockup_files = set()

    for key, values in config.items():
        if not key.startswith('_'):  # Pomijamy metadane
            # Klucz to plik wejściowy (np. "1.png")
            input_files.add(key)

            # Wartości to lista mockupów (np. ["canvas.psd", "frame.psd"])
            for mockup in values:
                mockup_files.add(mockup)

    return input_files, mockup_files

def check_files_existence():
    """Sprawdza istnienie wszystkich plików"""
    print("🔍 Sprawdzanie istnienia plików...")
    print(f"📁 Folder input: {input_folder}")
    print(f"📁 Folder mockup: {mockup_folder}")
    print(f"📄 Config: {config_file}")
    print()

    # Wczytaj pliki z folderów
    input_files_in_folder = get_folder_files(input_folder)
    mockup_files_in_folder = get_folder_files(mockup_folder)

    # Wczytaj mapowania z config.json
    input_files_in_config, mockup_files_in_config = load_config_mappings(config_file)

    print("📊 Statystyki:")
    print(f"   Plików wejściowych w config.json: {len(input_files_in_config)}")
    print(f"   Plików wejściowych w folderze input: {len(input_files_in_folder)}")
    print(f"   Plików mockup w config.json: {len(mockup_files_in_config)}")
    print(f"   Plików mockup w folderze mockup: {len(mockup_files_in_folder)}")
    print()

    # Sprawdź pliki wejściowe
    missing_input_files = input_files_in_config - input_files_in_folder
    extra_input_files = input_files_in_folder - input_files_in_config

    # Sprawdź pliki mockup
    missing_mockup_files = mockup_files_in_config - mockup_files_in_folder
    extra_mockup_files = mockup_files_in_folder - mockup_files_in_config

    # Wyniki
    all_good = True

    if missing_input_files:
        all_good = False
        print("❌ BRAKUJĄCE PLIKI WEJŚCIOWE (w config.json ale nie w folderze input):")
        for file in sorted(missing_input_files):
            print(f"   - {file}")
        print()

    if missing_mockup_files:
        all_good = False
        print("❌ BRAKUJĄCE PLIKI MOCKUP (w config.json ale nie w folderze mockup):")
        for file in sorted(missing_mockup_files):
            print(f"   - {file}")
        print()

    if extra_input_files:
        print("⚠️  DODATKOWE PLIKI WEJŚCIOWE (w folderze input ale nie w config.json):")
        for file in sorted(extra_input_files):
            print(f"   + {file}")
        print()

    if extra_mockup_files:
        print("⚠️  DODATKOWE PLIKI MOCKUP (w folderze mockup ale nie w config.json):")
        for file in sorted(extra_mockup_files):
            print(f"   + {file}")
        print()

    if all_good:
        print("✅ WSZYSTKO W PORZĄDKU!")
        print("   Wszystkie pliki z config.json istnieją w odpowiednich folderach.")
    else:
        print("⚠️  ZNALEZIONO PROBLEMY!")
        print("   Niektóre pliki z config.json nie istnieją w folderach.")

    return all_good

if __name__ == "__main__":
    check_files_existence()