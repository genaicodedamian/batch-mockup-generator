import csv
import re
from pathlib import Path

# Ścieżka do pliku CSV
csv_file = Path("/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/GRAFIKI BLESSYOU MIGRACJA.csv")

# Możliwe warianty bazowego URL
base_urls = [
    "https://blessyou.pl//wp-content/uploads/my-images/art/",
    "https://blessyou.pl/wp-content/uploads/my-images/art/"
]
extension = ".webp"

# Zbiór do przechowywania unikalnych wyoczyszczonych URLów
unique_images = set()

# Wczytaj plik CSV i przetwórz kolumnę 'Images'
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        images_cell = row.get('Images', '')
        
        if images_cell and images_cell.strip():
            # Podziel komórkę na poszczególne URLe (rozdzielone ", ")
            urls = [url.strip() for url in images_cell.split(', ')]
            
            for url in urls:
                if url:
                    # Usuń część bazową URL (spróbuj obu wariantów)
                    cleaned = url
                    for base_url in base_urls:
                        if cleaned.startswith(base_url):
                            cleaned = cleaned[len(base_url):]
                            break
                    
                    # Usuń rozszerzenie .webp
                    if cleaned.endswith(extension):
                        cleaned = cleaned[:-len(extension)]
                    
                    # Dodaj do zbioru
                    if cleaned:
                        unique_images.add(cleaned)

# Posortuj dla czytelności
sorted_images = sorted(unique_images)

# Wyświetl wyniki
print(f"Liczba unikalnych obrazów: {len(sorted_images)}\n")
print("Oczyszczone URLe:")
print("-" * 50)
for img in sorted_images:
    print(img)

# Opcjonalnie: zapisz do pliku
output_file = Path("/Users/damianaugustyn/Documents/projects/Smart PS replacer/extract/extract_art/extracted_images.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"Liczba unikalnych obrazów: {len(sorted_images)}\n\n")
    for img in sorted_images:
        f.write(f"{img}\n")

print(f"\n✓ Wyniki zapisane do: {output_file}")
