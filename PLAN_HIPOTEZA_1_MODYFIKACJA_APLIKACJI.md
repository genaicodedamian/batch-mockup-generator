# Plan Implementacji - Hipoteza 1: Modyfikacja Aplikacji macOS

## Podsumowanie
Najprostsze rozwiązanie - modyfikacja tylko aplikacji macOS, bez zmian w skrypcie silnika. Aplikacja generuje osobny obiekt mockup dla każdej kombinacji input→mockup określonej w `config.json`.

---

## Zalety ✅
- ✅ **Brak modyfikacji skryptu silnika** - wykorzystujemy istniejącą, przetestowaną logikę
- ✅ **Najprostsza implementacja** - zmiany tylko w jednym miejscu
- ✅ **Bezpieczna** - nie ryzykujemy złamania istniejącej funkcjonalności
- ✅ **Szybka do wdrożenia** - minimalna ilość kodu do napisania
- ✅ **Łatwa do debugowania** - prosta logika, łatwo śledzić przepływ
- ✅ **Zgodna z obecną architekturą** - nie wymaga refaktoryzacji

## Wady ❌
- ❌ **Wielokrotne otwieranie tego samego PSD** - jeśli mockup ma wiele przypisań
- ❌ **Dłuższy czas wykonania** - każde otwarcie PSD to ~1-3 sekundy
- ❌ **Większy plik wyjściowy JSX** - więcej obiektów w tablicy mockups
- ❌ **Większe zużycie pamięci** - Photoshop wielokrotnie ładuje ten sam plik

---

## Analiza config.json

### Obecna struktura:
```json
{
  "1.png": ["1.psd", "2.psd"],
  "2.png": ["2.psd", "3.psd"],
  "3.png": ["1.psd", "3.psd"]
}
```

### Interpretacja:
- **Klucz**: nazwa pliku z folderu `input/` (bez względu na faktyczne rozszerzenie)
- **Wartość**: tablica nazw plików mockup z folderu `mockup/`

### Mapowanie kombinacji:
1. `1.png` (faktycznie `1.jpeg`) → `mockup/1.psd`
2. `1.png` (faktycznie `1.jpeg`) → `mockup/2.psd`
3. `2.png` (faktycznie `2.jpeg`) → `mockup/2.psd`
4. `2.png` (faktycznie `2.jpeg`) → `mockup/3.psd`
5. `3.png` (faktycznie `3.jpeg`) → `mockup/1.psd`
6. `3.png` (faktycznie `3.jpeg`) → `mockup/3.psd`

**Wynik: 6 plików wyjściowych** (zamiast obecnych 9)

---

## Obecna struktura `main_mockup_generator.jsx`

### Jak jest teraz:
```javascript
mockups([
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/1.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',  // ← cały folder
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  // Kolejne 2 mockupy dla 2.psd i 3.psd
]);
```

### Jak będzie po zmianach:
```javascript
mockups([
  // 1.jpeg → 1.psd
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/1.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: ['/path/to/input/1.jpeg'],  // ← konkretny plik jako tablica
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  
  // 1.jpeg → 2.psd
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/2.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: ['/path/to/input/1.jpeg'],  // ← konkretny plik jako tablica
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  
  // 2.jpeg → 2.psd
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/2.psd',  // ← ten sam mockup ponownie
    smartObjects: [
      {
        target: 'Frame 1',
        input: ['/path/to/input/2.jpeg'],
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  
  // ... itd. dla pozostałych kombinacji
]);
```

---

## Szczegółowy Plan Implementacji

### Krok 1: Analiza aplikacji macOS
**Lokalizacja:** `SmartMockupCreator/SmartMockupCreator/`

#### Pliki do przeanalizowania:
1. ✅ **JSXGeneratorService.swift** - główny generator skryptu
2. ✅ **MockupGeneratorView.swift** - interfejs użytkownika
3. ✅ **ValidationService.swift** - walidacja danych wejściowych

#### Pytania do rozstrzygnięcia:
- [ ] Gdzie w kodzie Swift generowany jest plik JSX?
- [ ] Jak obecnie aplikacja iteruje przez mockupy?
- [ ] Czy config.json jest już gdzieś wczytywany?
- [ ] Jaka jest struktura danych przed generowaniem JSX?

---

### Krok 2: Dodanie obsługi config.json

#### 2.1. Definicja struktury danych (Swift)
```swift
// W JSXGeneratorService.swift lub nowym pliku ConfigParser.swift

struct ConfigMapping: Codable {
    // Typ: [String: [String]]
    // Przykład: ["1.png": ["1.psd", "2.psd"]]
}

struct MockupCombination {
    let inputFile: String      // np. "1.jpeg"
    let mockupFile: String     // np. "1.psd"
    let inputPath: String      // pełna ścieżka do input
    let mockupPath: String     // pełna ścieżka do mockup
}
```

#### 2.2. Wczytanie config.json
```swift
func loadConfigMapping(from configPath: String) throws -> [String: [String]] {
    let configURL = URL(fileURLWithPath: configPath)
    let data = try Data(contentsOf: configURL)
    let decoder = JSONDecoder()
    return try decoder.decode([String: [String]].self, from: data)
}
```

#### 2.3. Parsowanie do kombinacji
```swift
func parseConfigToCombinations(
    config: [String: [String]],
    inputFolder: String,
    mockupFolder: String
) -> [MockupCombination] {
    var combinations: [MockupCombination] = []
    
    for (inputKey, mockupFiles) in config {
        // Znajdź faktyczny plik w folderze input
        let actualInputFile = findActualFile(
            named: inputKey, 
            inFolder: inputFolder
        )
        
        guard let inputFile = actualInputFile else {
            print("WARNING: Input file not found for key: \(inputKey)")
            continue
        }
        
        // Dla każdego mockupa w tablicy
        for mockupFile in mockupFiles {
            let mockupPath = "\(mockupFolder)/\(mockupFile)"
            
            // Sprawdź czy mockup istnieje
            guard FileManager.default.fileExists(atPath: mockupPath) else {
                print("WARNING: Mockup file not found: \(mockupPath)")
                continue
            }
            
            combinations.append(MockupCombination(
                inputFile: inputFile.name,
                mockupFile: mockupFile,
                inputPath: inputFile.path,
                mockupPath: mockupPath
            ))
        }
    }
    
    return combinations
}

func findActualFile(named: String, inFolder: String) -> (name: String, path: String)? {
    let baseNameWithoutExt = named.replacingOccurrences(
        of: #"\.[^.]+$"#, 
        with: "", 
        options: .regularExpression
    )
    
    let fm = FileManager.default
    guard let files = try? fm.contentsOfDirectory(atPath: inFolder) else {
        return nil
    }
    
    // Szukaj pliku z tym samym basename
    for file in files {
        let fileBase = file.replacingOccurrences(
            of: #"\.[^.]+$"#, 
            with: "", 
            options: .regularExpression
        )
        
        if fileBase == baseNameWithoutExt {
            return (name: file, path: "\(inFolder)/\(file)")
        }
    }
    
    return nil
}
```

---

### Krok 3: Modyfikacja generatora JSX

#### 3.1. Zmiana logiki generowania
**Przed (obecnie):**
```swift
// Pseudokod obecnej logiki
for mockup in mockupFiles {
    generate_mockup_object {
        mockupPath: mockup
        smartObjects: [
            {
                input: entire_input_folder
            }
        ]
    }
}
```

**Po:**
```swift
// Nowa logika
let combinations = parseConfigToCombinations(
    config: loadedConfig,
    inputFolder: inputFolderPath,
    mockupFolder: mockupFolderPath
)

for combination in combinations {
    generate_mockup_object {
        mockupPath: combination.mockupPath
        smartObjects: [
            {
                input: [combination.inputPath]  // ← tablica z jednym plikiem
            }
        ]
    }
}
```

#### 3.2. Implementacja w JSXGeneratorService.swift
```swift
func generateJSXScript(
    inputFolder: String,
    mockupFolder: String,
    outputFolder: String,
    configPath: String,
    // ... inne parametry
) -> String {
    
    // 1. Wczytaj config.json
    guard let config = try? loadConfigMapping(from: configPath) else {
        // Fallback do starej logiki jeśli config nie istnieje
        return generateJSXScriptLegacy(...)
    }
    
    // 2. Parsuj do kombinacji
    let combinations = parseConfigToCombinations(
        config: config,
        inputFolder: inputFolder,
        mockupFolder: mockupFolder
    )
    
    // 3. Generuj JSX
    var jsxContent = generateJSXHeader()
    jsxContent += generateOutputOptions(outputFolder: outputFolder)
    jsxContent += "\nmockups([\n"
    
    // 4. Dla każdej kombinacji generuj obiekt mockup
    for (index, combo) in combinations.enumerated() {
        jsxContent += generateMockupObject(
            mockupPath: combo.mockupPath,
            inputPath: combo.inputPath,
            smartObjectName: smartObjectName,
            align: align,
            resize: resize
        )
        
        // Przecinek między obiektami (oprócz ostatniego)
        if index < combinations.count - 1 {
            jsxContent += ",\n\n"
        }
    }
    
    jsxContent += "\n]);\n"
    jsxContent += generateJSXFooter(count: combinations.count)
    
    return jsxContent
}

func generateMockupObject(
    mockupPath: String,
    inputPath: String,
    smartObjectName: String,
    align: String,
    resize: String
) -> String {
    return """
      {
        output: outputOpts,
        mockupPath: '\(mockupPath)',
        smartObjects: [
          {
            target: '\(smartObjectName)',
            input: ['\(inputPath)'],
            align: '\(align)',
            resize: '\(resize)'
          }
        ]
      }
    """
}
```

---

### Krok 4: Walidacja i error handling

#### 4.1. Walidacja config.json
```swift
enum ConfigValidationError: Error {
    case fileNotFound
    case invalidJSON
    case emptyConfig
    case inputFileNotFound(String)
    case mockupFileNotFound(String)
    case noValidCombinations
}

func validateConfig(
    configPath: String,
    inputFolder: String,
    mockupFolder: String
) throws -> [MockupCombination] {
    
    // 1. Sprawdź czy config.json istnieje
    guard FileManager.default.fileExists(atPath: configPath) else {
        throw ConfigValidationError.fileNotFound
    }
    
    // 2. Wczytaj i parsuj JSON
    guard let config = try? loadConfigMapping(from: configPath) else {
        throw ConfigValidationError.invalidJSON
    }
    
    // 3. Sprawdź czy config nie jest pusty
    guard !config.isEmpty else {
        throw ConfigValidationError.emptyConfig
    }
    
    // 4. Parsuj do kombinacji (z walidacją)
    let combinations = parseConfigToCombinations(
        config: config,
        inputFolder: inputFolder,
        mockupFolder: mockupFolder
    )
    
    // 5. Sprawdź czy mamy jakiekolwiek poprawne kombinacje
    guard !combinations.isEmpty else {
        throw ConfigValidationError.noValidCombinations
    }
    
    return combinations
}
```

#### 4.2. Obsługa błędów w UI
```swift
// W MockupGeneratorView.swift

func generateScript() {
    do {
        let combinations = try validateConfig(
            configPath: configPath,
            inputFolder: inputFolder,
            mockupFolder: mockupFolder
        )
        
        let jsxScript = generateJSXScript(combinations: combinations)
        
        // Zapisz i uruchom
        saveAndExecuteScript(jsxScript)
        
    } catch ConfigValidationError.fileNotFound {
        showError("Config file not found at: \(configPath)")
    } catch ConfigValidationError.invalidJSON {
        showError("Invalid JSON format in config.json")
    } catch ConfigValidationError.noValidCombinations {
        showError("No valid combinations found. Check if files exist.")
    } catch {
        showError("Unexpected error: \(error.localizedDescription)")
    }
}
```

---

### Krok 5: Nazewnictwo plików wyjściowych

#### Problem:
Gdy ten sam mockup jest używany z różnymi plikami input, potrzebujemy unikalnych nazw.

#### Rozwiązanie:
Wykorzystaj istniejące słowo kluczowe `@input` w `output.filename`:

```javascript
var outputOpts = {
  path: '/path/to/output',
  format: 'jpg',
  zeroPadding: true,
  filename: '@input_@mockup'  // ← zostaje bez zmian
};
```

#### Przykładowe wyjście:
- `1.jpeg` + `1.psd` → `1_1.jpg`
- `1.jpeg` + `2.psd` → `1_2.jpg`
- `2.jpeg` + `2.psd` → `2_2.jpg`
- `2.jpeg` + `3.psd` → `2_3.jpg`
- `3.jpeg` + `1.psd` → `3_1.jpg`
- `3.jpeg` + `3.psd` → `3_3.jpg`

**Uwaga:** Jeśli chcesz inny format nazewnictwa, możesz to zmienić w aplikacji.

---

### Krok 6: Testowanie

#### 6.1. Testy jednostkowe (Swift)
```swift
import XCTest

class ConfigParserTests: XCTestCase {
    
    func testLoadConfigMapping() {
        let config = try? loadConfigMapping(from: "test_config.json")
        XCTAssertNotNil(config)
        XCTAssertEqual(config?["1.png"]?.count, 2)
    }
    
    func testParseConfigToCombinations() {
        let config = ["1.png": ["1.psd", "2.psd"]]
        let combinations = parseConfigToCombinations(
            config: config,
            inputFolder: "/test/input",
            mockupFolder: "/test/mockup"
        )
        XCTAssertEqual(combinations.count, 2)
    }
    
    func testFindActualFile() {
        // Test że "1.png" w config znajduje "1.jpeg" w folderze
        let result = findActualFile(named: "1.png", inFolder: testInputFolder)
        XCTAssertEqual(result?.name, "1.jpeg")
    }
}
```

#### 6.2. Test integracyjny
1. Przygotuj testowe dane:
   ```
   test/
   ├── config.json
   ├── input/
   │   ├── 1.jpeg
   │   ├── 2.jpeg
   │   └── 3.jpeg
   └── mockup/
       ├── 1.psd
       ├── 2.psd
       └── 3.psd
   ```

2. Uruchom aplikację z testowymi danymi

3. Sprawdź wygenerowany JSX:
   - Czy zawiera 6 obiektów mockup?
   - Czy każdy ma prawidłową ścieżkę input?
   - Czy kombinacje są zgodne z config.json?

4. Uruchom wygenerowany skrypt w Photoshop

5. Sprawdź output:
   - Czy utworzono dokładnie 6 plików?
   - Czy nazwy są poprawne?
   - Czy zawartość jest prawidłowa?

---

### Krok 7: Optymalizacja (opcjonalnie)

#### 7.1. Grupowanie mockupów
Aby zredukować wielokrotne otwieranie tego samego PSD:

```swift
func groupCombinationsByMockup(
    _ combinations: [MockupCombination]
) -> [String: [MockupCombination]] {
    var grouped: [String: [MockupCombination]] = [:]
    
    for combo in combinations {
        if grouped[combo.mockupPath] == nil {
            grouped[combo.mockupPath] = []
        }
        grouped[combo.mockupPath]?.append(combo)
    }
    
    return grouped
}
```

**Uwaga:** To nie rozwiąże problemu wielokrotnego otwierania, ale może być przydatne do statystyk/raportowania.

---

## Harmonogram Implementacji

### Faza 1: Przygotowanie (1-2 godziny)
- [ ] Analiza kodu aplikacji macOS
- [ ] Zidentyfikowanie miejsca generowania JSX
- [ ] Stworzenie testowego środowiska

### Faza 2: Implementacja Core (3-4 godziny)
- [ ] Implementacja `loadConfigMapping()`
- [ ] Implementacja `parseConfigToCombinations()`
- [ ] Implementacja `findActualFile()`
- [ ] Modyfikacja generatora JSX

### Faza 3: Walidacja i Error Handling (2-3 godziny)
- [ ] Implementacja walidacji config.json
- [ ] Dodanie obsługi błędów w UI
- [ ] Dodanie komunikatów użytkownikowi

### Faza 4: Testowanie (2-3 godziny)
- [ ] Testy jednostkowe
- [ ] Test integracyjny end-to-end
- [ ] Testy edge cases

### Faza 5: Dokumentacja (1 godzina)
- [ ] Aktualizacja README
- [ ] Dokumentacja formatu config.json
- [ ] Przykłady użycia

**Szacowany czas całkowity: 9-13 godzin**

---

## Edge Cases i Rozwiązania

### 1. Plik w config.json nie istnieje w folderze
**Rozwiązanie:** 
- Wypisz warning w console
- Pomiń tę kombinację
- Kontynuuj z pozostałymi

### 2. Config.json nie istnieje
**Rozwiązanie:**
- Fallback do starej logiki (każdy input na każdy mockup)
- LUB: Wyświetl błąd i wymagaj config.json

### 3. Różne rozszerzenia plików
**Rozwiązanie:**
- W config.json używaj nazwy bazowej (np. "1.png")
- W kodzie szukaj po basename bez rozszerzenia
- Dopasuj do faktycznego pliku (np. "1.jpeg")

### 4. Pusta tablica mockupów w config.json
```json
{
  "1.png": []
}
```
**Rozwiązanie:**
- Pomiń ten klucz
- Wypisz warning

### 5. Duplikaty kombinacji
```json
{
  "1.png": ["1.psd", "1.psd"]
}
```
**Rozwiązanie:**
- Usuń duplikaty przy parsowaniu
- LUB: Pozwól na duplikaty (użytkownik może mieć powód)

---

## Wymagania Systemowe

### Aplikacja macOS:
- Swift 5.5+
- macOS 12.0+
- Xcode 13.0+

### Photoshop:
- Adobe Photoshop CC 2019 lub nowszy
- Obsługa ExtendScript

### Struktura folderów:
```
Project/
├── config.json           ← WYMAGANY
├── input/               ← pliki obrazów
├── mockup/              ← pliki PSD/PSB
└── output/              ← generowane automatycznie
```

---

## Migracja z obecnego rozwiązania

### Krok 1: Stwórz config.json
Dla obecnej logiki (każdy input na każdy mockup):
```json
{
  "1.jpeg": ["1.psd", "2.psd", "3.psd"],
  "2.jpeg": ["1.psd", "2.psd", "3.psd"],
  "3.jpeg": ["1.psd", "2.psd", "3.psd"]
}
```

### Krok 2: Przetestuj z nowym kodem
Wynik powinien być identyczny jak obecnie (9 plików).

### Krok 3: Dostosuj config.json do nowych potrzeb
```json
{
  "1.jpeg": ["1.psd", "2.psd"],
  "2.jpeg": ["2.psd", "3.psd"],
  "3.jpeg": ["1.psd", "3.psd"]
}
```

### Krok 4: Wygeneruj ponownie
Teraz powinno być tylko 6 plików.

---

## Dodatkowe Uwagi

### Kompatybilność wstecz
Jeśli chcesz zachować kompatybilność ze starym zachowaniem:

```swift
func generateJSXScript(...) -> String {
    // Sprawdź czy config.json istnieje
    if FileManager.default.fileExists(atPath: configPath) {
        // Użyj nowej logiki
        return generateJSXScriptWithConfig(...)
    } else {
        // Fallback do starej logiki
        return generateJSXScriptLegacy(...)
    }
}
```

### Performance
- Każde otwarcie PSD: ~1-3 sekundy
- Dla config.json z przykładu: 6 otworzeń
- Szacowany czas: ~6-18 sekund
- W praktyce: `1.psd` otwarty 2x, `2.psd` otwarty 2x, `3.psd` otwarty 2x

### Rekomendacja
To podejście jest **najlepsze dla małych projektów** (do ~20 plików wyjściowych).
Dla większych projektów rozważ Hipotezę 2 lub 3.

---

## Checklist przed rozpoczęciem

- [ ] Backup obecnej aplikacji
- [ ] Przygotuj testowe dane
- [ ] Zainstaluj Xcode
- [ ] Zrozum obecny przepływ aplikacji
- [ ] Przeczytaj dokumentację Swift Codable
- [ ] Zapoznaj się z API FileManager

---

## Następne kroki

Po implementacji tego podejścia, możesz rozważyć:
1. Dodanie UI do tworzenia/edycji config.json
2. Podgląd kombinacji przed generowaniem
3. Eksport raportu z wygenerowanych plików
4. Historię ostatnich konfiguracji

---

*Dokument stworzony: 2025-10-30*
*Wersja: 1.0*
