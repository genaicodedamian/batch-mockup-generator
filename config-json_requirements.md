# Wymagania dla pliku `config.json`

**Autor:** GitHub Copilot
**Data:** 2025-10-31
**Projekt:** Smart PS Replacer

## 1. Kontekst i cel pliku `config.json`

W naszym systemie działa skrypt Adobe Photoshop o nazwie `main_mockup_generator.jsx`, który automatyzuje proces tworzenia mockupów. Skrypt ten operuje na zdefiniowanej strukturze folderów:
-   `input/` - zawiera pliki graficzne (np. projekty plakatów).
-   `mockup/` - zawiera szablony mockupów (pliki `.psd`).
-   `output/` - do tego folderu zapisywane są finalne obrazy.

**Głównym celem pliku `config.json` jest precyzyjne instruowanie tego skryptu, które pliki z folderu `input/` mają zostać umieszczone w których szablonach z folderu `mockup/`.**

Plik ten jest jedynym źródłem prawdy (`Single Source of Truth`) dla logiki mapowania i musi być generowany zgodnie z poniższymi wytycznymi.

## 2. Struktura i wymagania

Plik musi być poprawnym formatem JSON i składać się z par klucz-wartość.

```json
{
  "NAZWA_PLIKU_WEJSCIOWEGO.png": ["mockup1.psd", "mockup2.psd"],
  "inny_plik.png": ["mockup1.psd", "mockup3.psd"]
}
```

### Klucz (`key`)

-   **Typ:** `String`
-   **Format:** Musi być nazwą pliku z rozszerzeniem `.png` (np. `"obraz123.png"`).
-   **Przeznaczenie:** Reprezentuje plik wejściowy z folderu `input/`. Mimo że skrypt technicznie dopasowuje pliki po nazwie bazowej (ignorując rozszerzenie), **wymogiem jest, aby wszystkie klucze w `config.json` miały rozszerzenie `.png`**.

### Wartość (`value`)

-   **Typ:** `Array` (tablica ciągów znaków).
-   **Format:** Każdy element w tablicy musi być nazwą pliku z rozszerzeniem `.psd` (np. `"szablon_A.psd"`).
-   **Przeznaczenie:** Reprezentuje plik szablonu mockupu z folderu `mockup/`.

### Pola meta (opcjonalne)

-   Klucze rozpoczynające się od znaku podkreślenia (`_`), np. `_comment`, `_description`, są **ignorowane** przez skrypt i mogą być używane do celów dokumentacyjnych.

## 3. Przykład praktyczny

Poniższa konfiguracja:

```json
{
  "_comment": "Konfiguracja dla kolekcji odzieży",
  "jezus_white_front.png": ["sweatshirt_white_back.psd", "sweatshirt_white_back2.psd"],
  "duchswiety_black_hoodie.png": ["hoodie_black_front.psd", "hoodie_black_closeup.psd"],
  "duchswiety_black_back.png": ["hoodie_black_back.psd"]
}
```

Spowoduje, że skrypt `main_mockup_generator.jsx` wygeneruje **pięć** plików wynikowych w folderze `output/`:

1.  `jezus_white_front_sweatshirt_white_back.jpg`
2.  `jezus_white_front_sweatshirt_white_back2.jpg`
3.  `duchswiety_black_hoodie_hoodie_black_front.jpg`
4.  `duchswiety_black_hoodie_hoodie_black_closeup.jpg`
5.  `duchswiety_black_back_hoodie_black_back.jpg`

## 4. Podsumowanie wymagań dla generatora `config.json`

1.  **Format:** Wygenerowany plik musi być walidowalnym JSON-em.
2.  **Klucze:** Muszą być stringami zakończonymi na `.png`.
3.  **Wartości:** Muszą być tablicami stringów, gdzie każdy string jest zakończony na `.psd`.
4.  **Walidacja:** Skrypt wykonawczy sam weryfikuje istnienie plików w folderach `input/` i `mockup/`. Generator `config.json` nie musi tego robić, ale musi trzymać się ścisłego formatu klucz-wartość.
