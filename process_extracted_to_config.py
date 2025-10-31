#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do przetworzenia extracted_images.txt do formatu config.json
Zachowuje metadane i tworzy mapowania zgodnie z wymaganiami
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Ścieżki do plików
project_folder = Path("/Users/damianaugustyn/Documents/projects/Smart PS replacer")
extracted_file = project_folder / "extract" / "extract_art" / "extracted_images.txt"
config_file = project_folder / "config.json"

def parse_extracted_images(file_path):
    """
    Parsuje plik extracted_images.txt i zwraca słownik grupujący mockupy według nazw plików wejściowych
    """
    mappings = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Pomiń puste linie i linię z liczbą obrazów
            if not line or line.startswith("Liczba unikalnych obrazów:"):
                continue
            
            # Sprawdź czy linia zawiera separator "_"
            if "_" not in line:
                print(f"Ostrzeżenie: Pomijam linię bez separatora '_': {line}")
                continue
            
            # Podziel na nazwę pliku wejściowego i mockupu
            parts = line.split("_", 1)  # Podziel tylko na pierwszy "_"
            if len(parts) != 2:
                print(f"Ostrzeżenie: Nieprawidłowy format linii: {line}")
                continue
            
            input_name, mockup_name = parts
            
            # Dodaj rozszerzenia
            input_key = f"{input_name}.png"
            mockup_value = f"{mockup_name}.psd"
            
            # Dodaj do mapowania (unikaj duplikatów)
            if mockup_value not in mappings[input_key]:
                mappings[input_key].append(mockup_value)
    
    return dict(mappings)

def create_config_json(mappings, output_path):
    """
    Tworzy nowy config.json z zachowaniem metadanych
    """
    # Metadane do zachowania
    config_data = {
        "_comment": "=== MOCKUP CONFIGURATION FILE ===",
        "_description": "This file defines which input files should be applied to which mockup files",
        "_format": {
            "key": "Input filename (can use any extension, e.g., '1.png' will match '1.jpeg')",
            "value": "Array of mockup filenames from the 'mockup' folder"
        },
        "_example": {
            "input-file.png": ["mockup1.psd", "mockup2.psd"],
            "another-input.jpg": ["mockup3.psd"]
        },
        "_notes": [
            "Keys match by basename (without extension): '1.png' matches '1.jpeg', '1.jpg', etc.",
            "Values are arrays of mockup filenames (must exist in 'mockup' folder)",
            "Each key-value pair creates N output files (N = array length)",
            "Output files are named: inputBasename_mockupBasename.jpg"
        ],
        "_lastModified": datetime.now().strftime("%Y-%m-%d"),
        "_generatedFrom": "extracted_images.txt",
        "_totalInputFiles": len(mappings),
        "_totalCombinations": sum(len(mockups) for mockups in mappings.values())
    }
    
    # Dodaj mapowania (posortowane alfabetycznie dla czytelności)
    def sort_key(key):
        """Funkcja sortująca klucze - najpierw numeryczne, potem alfabetyczne"""
        base_name = key.split('.')[0]
        if base_name.isdigit():
            return (0, int(base_name))  # Numeryczne najpierw
        else:
            return (1, base_name)  # Alfabetyczne potem
    
    for input_key in sorted(mappings.keys(), key=sort_key):
        # Posortuj mockupy alfabetycznie
        config_data[input_key] = sorted(mappings[input_key])
    
    # Zapisz do pliku
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

def main():
    print("🚀 Przetwarzanie extracted_images.txt do config.json...")
    print(f"📁 Źródło: {extracted_file}")
    print(f"📁 Cel: {config_file}")
    
    # Sprawdź czy plik źródłowy istnieje
    if not extracted_file.exists():
        print(f"❌ Błąd: Plik {extracted_file} nie istnieje!")
        return
    
    # Parsuj plik
    print("\n📖 Parsowanie extracted_images.txt...")
    mappings = parse_extracted_images(extracted_file)
    
    # Pokaż statystyki
    total_inputs = len(mappings)
    total_combinations = sum(len(mockups) for mockups in mappings.values())
    
    print(f"✅ Pomyślnie sparsowano:")
    print(f"   📄 Plików wejściowych: {total_inputs}")
    print(f"   🔄 Całkowita liczba kombinacji: {total_combinations}")
    
    # Pokaż przykłady mapowań
    print(f"\n📋 Przykłady mapowań (pierwsze 5):")
    for i, (input_key, mockups) in enumerate(sorted(mappings.items())[:5]):
        print(f"   {input_key}: {mockups}")
    
    if total_inputs > 5:
        print(f"   ... i {total_inputs - 5} więcej")
    
    # Utwórz config.json
    print(f"\n💾 Tworzenie config.json...")
    create_config_json(mappings, config_file)
    
    print(f"✅ Pomyślnie utworzono {config_file}")
    print(f"📊 Zawiera {total_inputs} plików wejściowych i {total_combinations} kombinacji")
    
    # Pokaż rozmiar pliku
    file_size = config_file.stat().st_size
    print(f"📏 Rozmiar pliku: {file_size:,} bajtów")
    
    print("\n🎉 Gotowe! Config.json został pomyślnie wygenerowany.")

if __name__ == "__main__":
    main()