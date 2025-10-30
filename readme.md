# Smart PS Replacer - Zautomatyzowany System Tworzenia Mockupów i Konwersji Obrazów

Ten projekt to zintegrowany zestaw narzędzi zaprojektowany do automatyzacji procesu tworzenia mockupów w programie Adobe Photoshop oraz optymalizacji wygenerowanych plików graficznych na potrzeby internetu.

## 🚀 Główne Cele Projektu

- **Automatyzacja**: Zastąpienie ręcznego i powtarzalnego procesu tworzenia mockupów dynamicznym skryptem.
- **Elastyczność**: Umożliwienie użytkownikowi precyzyjnego definiowania, które obrazy wejściowe mają być użyte w których plikach mockupów.
- **Efektywność**: Optymalizacja końcowych plików graficznych poprzez konwersję do nowoczesnego formatu WebP.

## ⚙️ Przepływ Pracy (Workflow)

Proces pracy z projektem składa się z trzech prostych kroków:

### Krok 1: Konfiguracja mapowań w `config.json`

Wszystko zaczyna się od pliku `config.json`. W tym miejscu definiujesz, które pliki wejściowe (np. `1.png`) mają zostać umieszczone w których szablonach mockupów (np. `1.psd`, `2.psd`).

**Przykład `config.json`:**
```json
{
  "1.png": ["1.psd", "2.psd"],
  "2.png": ["2.psd", "3.psd"],
  "3.png": ["1.psd", "3.psd"]
}
```
Dzięki tej konfiguracji skrypt wygeneruje dokładnie 6 zdefiniowanych kombinacji, a nie wszystkie 9 możliwych.

### Krok 2: Generowanie mockupów w Photoshopie

Uruchom skrypt `main_mockup_generator.jsx` w programie Adobe Photoshop (`Plik > Skrypty > Przeglądaj...`). Skrypt automatycznie:
1.  Odczyta konfigurację z `config.json`.
2.  Otworzy odpowiednie pliki mockupów.
3.  Umieści w nich zdefiniowane obrazy wejściowe.
4.  Zapisze gotowe pliki (domyślnie jako JPG) w folderze `output/`.

### Krok 3: Konwersja obrazów do formatu WebP

Po wygenerowaniu plików `.jpg`, możesz je skonwertować do zoptymalizowanego formatu `.webp` za pomocą skryptu w folderze `convert to webp/`. Jest to idealne rozwiązanie do publikacji obrazów w internecie.

Szczegółowe instrukcje znajdują się w pliku `convert to webp/readme.md`.

## 🧩 Komponenty Projektu

### 1. Generator Mockupów (`main_mockup_generator.jsx`)

Główny skrypt sterujący, który dynamicznie tworzy mockupy na podstawie pliku `config.json`. Jest to serce automatyzacji, które eliminuje potrzebę ręcznego edytowania skryptów przy każdej zmianie.

- **Plik konfiguracyjny**: `config.json`
- **Silnik**: `macos-desktop-app-PS-batch-mockup/script/Batch Mockup Smart Object Replacement.jsx`
- **Dokumentacja implementacji**: `IMPLEMENTATION_SUMMARY.md`

### 2. Aplikacja macOS do generowania skryptów (`SmartMockupCreator`)

Projekt zawiera również aplikację desktopową na macOS, która służyła jako narzędzie do generowania bardziej złożonych skryptów `.jsx`. Obecnie główny przepływ pracy opiera się na dynamicznym skrypcie `main_mockup_generator.jsx`, jednak aplikacja i jej kod źródłowy pozostają częścią projektu.

- **Lokalizacja**: `macos-desktop-app-PS-batch-mockup/`
- **Instrukcja uruchomienia**: `macos-desktop-app-PS-batch-mockup/readme.md`

### 3. Konwerter do WebP (`convert to webp/`)

Zestaw skryptów w Pythonie do konwersji obrazów `.jpg` i `.png` do formatu `.webp`. Narzędzie to jest kluczowe dla optymalizacji grafik na strony internetowe, zmniejszając ich rozmiar przy zachowaniu wysokiej jakości.

- **Lokalizacja**: `convert to webp/`
- **Wymagania**: Python 3, ImageMagick
- **Instrukcja użycia**: `convert to webp/readme.md`
