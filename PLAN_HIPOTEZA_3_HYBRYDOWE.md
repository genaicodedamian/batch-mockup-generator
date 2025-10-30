# Plan Implementacji - Hipoteza 3: Rozwiązanie Hybrydowe

## Podsumowanie
Kompromis między prostotą a wydajnością - aplikacja macOS parsuje `config.json` i przekazuje filtr jako parametr do każdego mockupa. Skrypt silnika otrzymuje dedykowaną listę plików input bez potrzeby samodzielnego parsowania config.

---

## Zalety ✅
- ✅ **Wydajność jak Hipoteza 2** - każdy mockup otwierany tylko raz
- ✅ **Prostsze zmiany w silniku** - tylko dodanie obsługi nowego parametru
- ✅ **Logika w aplikacji** - łatwiej testować i debugować (Swift vs JSX)
- ✅ **Flexibility** - łatwo dodać UI do zarządzania filtrowaniem
- ✅ **Clean separation** - config parsing w aplikacji, wykonanie w silniku
- ✅ **Better error handling** - Swift ma lepsze narzędzia do walidacji
- ✅ **UI Preview** - można pokazać użytkownikowi kombinacje przed generowaniem

## Wady ❌
- ❌ **Zmiany w dwóch miejscach** - aplikacja macOS + skrypt silnika
- ❌ **Nowy parametr** - trzeba dodać do API mockupa
- ❌ **Kompatybilność** - stare skrypty nie będą używać filtrowania
- ❌ **Dokumentacja** - trzeba udokumentować nowy parametr

---

## Koncepcja

### Główna idea:
Aplikacja macOS jest "kontrolerem", który:
1. Wczytuje config.json
2. Parsuje go do struktury danych
3. Dla każdego mockupa określa listę przypisanych plików input
4. Przekazuje tę listę jako nowy parametr `inputFiles` do smartObject
5. Skrypt silnika respektuje ten parametr

### Przykład wygenerowanego JSX:
```javascript
mockups([
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/1.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',              // ← folder (jak dotychczas)
        inputFiles: ['1.jpeg', '3.jpeg'],      // ← NOWY parametr - lista plików do użycia
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/2.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',
        inputFiles: ['1.jpeg', '2.jpeg'],      // ← inna lista dla tego mockupa
        align: 'center center',
        resize: 'fill'
      }
    ]
  },
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/3.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',
        inputFiles: ['2.jpeg', '3.jpeg'],      // ← jeszcze inna lista
        align: 'center center',
        resize: 'fill'
      }
    ]
  }
]);
```

---

## Architektura

```
┌─────────────────────────────────────────┐
│     Aplikacja macOS (Swift)             │
│                                         │
│  1. UI: Użytkownik wybiera foldery     │
│  2. Wczytaj config.json                 │
│  3. Parsuj do struktury                 │
│  4. Waliduj pliki                       │
│  5. Zbuduj mapę mockup → input files    │
│  6. Wygeneruj JSX z inputFiles[]        │
│  7. Zapisz i uruchom JSX                │
└─────────────────────────────────────────┘
                    ↓
            (generowany JSX)
                    ↓
┌─────────────────────────────────────────┐
│   Skrypt Silnika (ExtendScript)         │
│                                         │
│  1. Dla każdego mockupa:                │
│     a. Otwórz PSD                       │
│     b. Dla każdego smartObject:         │
│        - Sprawdź czy jest inputFiles[]  │
│        - Jeśli TAK: użyj tylko tych     │
│        - Jeśli NIE: użyj wszystkich     │
│     c. Przetwórz i zapisz               │
│     d. Zamknij PSD                      │
└─────────────────────────────────────────┘
```

---

## Szczegółowy Plan Implementacji

### CZĘŚĆ A: Aplikacja macOS (Swift)

#### Krok 1: Definicja struktur danych (30 min)

**Plik:** `JSXGeneratorService.swift` lub nowy `ConfigService.swift`

```swift
// MARK: - Config Structures

/// Reprezentuje mapping z config.json
struct ConfigMapping: Codable {
    // Format: [String: [String]]
    // Przykład: ["1.png": ["1.psd", "2.psd"]]
}

/// Reprezentuje pojedynczą kombinację input → mockup
struct InputToMockupMapping {
    let inputFileName: String     // np. "1.jpeg"
    let mockupFileName: String    // np. "1.psd"
}

/// Reprezentuje mockup z przypisanymi plikami input
struct MockupWithInputs {
    let mockupPath: String                // pełna ścieżka do PSD
    let mockupName: String                // nazwa pliku (np. "1.psd")
    let assignedInputFiles: [String]      // lista przypisanych plików (np. ["1.jpeg", "3.jpeg"])
}
```

---

#### Krok 2: Parser config.json (1-2 godziny)

**Plik:** Nowy `ConfigService.swift`

```swift
import Foundation

class ConfigService {
    
    // MARK: - Errors
    enum ConfigError: LocalizedError {
        case fileNotFound
        case invalidJSON
        case emptyConfig
        case inputFileNotFound(String)
        case mockupFileNotFound(String)
        
        var errorDescription: String? {
            switch self {
            case .fileNotFound:
                return "Config file not found"
            case .invalidJSON:
                return "Invalid JSON format in config.json"
            case .emptyConfig:
                return "Config.json is empty"
            case .inputFileNotFound(let file):
                return "Input file not found: \(file)"
            case .mockupFileNotFound(let file):
                return "Mockup file not found: \(file)"
            }
        }
    }
    
    // MARK: - Load Config
    
    /// Wczytuje config.json z dysku
    static func loadConfig(from path: String) throws -> [String: [String]] {
        let url = URL(fileURLWithPath: path)
        
        guard FileManager.default.fileExists(atPath: path) else {
            throw ConfigError.fileNotFound
        }
        
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        let config = try decoder.decode([String: [String]].self, from: data)
        
        guard !config.isEmpty else {
            throw ConfigError.emptyConfig
        }
        
        return config
    }
    
    // MARK: - Build Mockup Mapping
    
    /// Konwertuje config.json do mapy mockup → [input files]
    static func buildMockupMapping(
        config: [String: [String]],
        inputFolder: String,
        mockupFolder: String
    ) throws -> [MockupWithInputs] {
        
        var mockupMap: [String: Set<String>] = [:] // używamy Set aby uniknąć duplikatów
        
        // Najpierw zbuduj mapę mockup → set(input files)
        for (inputKey, mockupList) in config {
            
            // Znajdź faktyczny plik w folderze input
            guard let actualInputFile = findActualFile(
                named: inputKey,
                inFolder: inputFolder
            ) else {
                print("WARNING: Input file not found for key '\(inputKey)'")
                continue
            }
            
            // Dla każdego mockupa w liście
            for mockupName in mockupList {
                let mockupPath = "\(mockupFolder)/\(mockupName)"
                
                // Sprawdź czy mockup istnieje
                guard FileManager.default.fileExists(atPath: mockupPath) else {
                    print("WARNING: Mockup file not found: \(mockupName)")
                    continue
                }
                
                // Dodaj do mapy
                if mockupMap[mockupName] == nil {
                    mockupMap[mockupName] = Set<String>()
                }
                mockupMap[mockupName]?.insert(actualInputFile)
            }
        }
        
        // Konwertuj mapę do tablicy MockupWithInputs
        var result: [MockupWithInputs] = []
        
        for (mockupName, inputFilesSet) in mockupMap {
            let mockupPath = "\(mockupFolder)/\(mockupName)"
            let inputFiles = Array(inputFilesSet).sorted() // posortuj alfabetycznie
            
            result.append(MockupWithInputs(
                mockupPath: mockupPath,
                mockupName: mockupName,
                assignedInputFiles: inputFiles
            ))
        }
        
        // Posortuj mockupy alfabetycznie
        result.sort { $0.mockupName < $1.mockupName }
        
        return result
    }
    
    // MARK: - Helper: Find Actual File
    
    /// Znajduje faktyczny plik w folderze na podstawie klucza z config
    /// Dopasowanie po basename (bez rozszerzenia)
    private static func findActualFile(named key: String, inFolder folder: String) -> String? {
        // Usuń rozszerzenie z klucza
        let baseName = key.replacingOccurrences(of: #"\.[^.]+$"#, with: "", options: .regularExpression)
        
        guard let files = try? FileManager.default.contentsOfDirectory(atPath: folder) else {
            return nil
        }
        
        // Szukaj pliku z tym samym basename
        for file in files {
            let fileBase = file.replacingOccurrences(of: #"\.[^.]+$"#, with: "", options: .regularExpression)
            
            if fileBase.lowercased() == baseName.lowercased() {
                return file
            }
        }
        
        return nil
    }
    
    // MARK: - Validation
    
    /// Waliduje config i sprawdza czy wszystkie pliki istnieją
    static func validateConfig(
        config: [String: [String]],
        inputFolder: String,
        mockupFolder: String
    ) -> (valid: Bool, warnings: [String]) {
        
        var warnings: [String] = []
        
        for (inputKey, mockupList) in config {
            
            // Sprawdź input file
            if findActualFile(named: inputKey, inFolder: inputFolder) == nil {
                warnings.append("Input file not found: \(inputKey)")
            }
            
            // Sprawdź mockup files
            for mockupName in mockupList {
                let mockupPath = "\(mockupFolder)/\(mockupName)"
                if !FileManager.default.fileExists(atPath: mockupPath) {
                    warnings.append("Mockup file not found: \(mockupName)")
                }
            }
        }
        
        return (warnings.isEmpty, warnings)
    }
}
```

---

#### Krok 3: Modyfikacja generatora JSX (2-3 godziny)

**Plik:** `JSXGeneratorService.swift`

```swift
class JSXGeneratorService {
    
    // MARK: - Generate JSX Script
    
    static func generateJSXScript(
        inputFolder: String,
        mockupFolder: String,
        outputFolder: String,
        configPath: String?,
        smartObjectName: String,
        outputFormat: String,
        alignment: String,
        resizeMode: String,
        enginePath: String
    ) -> String {
        
        var mockupsConfig: [MockupWithInputs] = []
        
        // Jeśli podano config.json, użyj go
        if let configPath = configPath,
           FileManager.default.fileExists(atPath: configPath) {
            
            do {
                // Wczytaj config
                let config = try ConfigService.loadConfig(from: configPath)
                
                // Waliduj
                let validation = ConfigService.validateConfig(
                    config: config,
                    inputFolder: inputFolder,
                    mockupFolder: mockupFolder
                )
                
                if !validation.valid {
                    print("Config validation warnings:")
                    validation.warnings.forEach { print("  - \($0)") }
                }
                
                // Zbuduj mapowanie
                mockupsConfig = try ConfigService.buildMockupMapping(
                    config: config,
                    inputFolder: inputFolder,
                    mockupFolder: mockupFolder
                )
                
                print("✅ Config loaded: \(mockupsConfig.count) mockups configured")
                
            } catch {
                print("❌ Error loading config: \(error.localizedDescription)")
                print("Falling back to default behavior (all inputs on all mockups)")
                mockupsConfig = [] // fallback
            }
        }
        
        // Jeśli nie ma config lub wystąpił błąd, użyj starej logiki
        if mockupsConfig.isEmpty {
            mockupsConfig = buildDefaultMockupMapping(
                inputFolder: inputFolder,
                mockupFolder: mockupFolder
            )
        }
        
        // Generuj JSX
        return buildJSXContent(
            mockupsConfig: mockupsConfig,
            inputFolder: inputFolder,
            outputFolder: outputFolder,
            smartObjectName: smartObjectName,
            outputFormat: outputFormat,
            alignment: alignment,
            resizeMode: resizeMode,
            enginePath: enginePath
        )
    }
    
    // MARK: - Build Default Mapping (Fallback)
    
    /// Stara logika: wszystkie mockupy przetwarzają wszystkie pliki input
    private static func buildDefaultMockupMapping(
        inputFolder: String,
        mockupFolder: String
    ) -> [MockupWithInputs] {
        
        var mockups: [MockupWithInputs] = []
        
        // Pobierz wszystkie mockupy
        guard let mockupFiles = try? FileManager.default.contentsOfDirectory(atPath: mockupFolder) else {
            return []
        }
        
        let psdFiles = mockupFiles.filter { $0.hasSuffix(".psd") || $0.hasSuffix(".psb") }
        
        for mockupName in psdFiles.sorted() {
            mockups.append(MockupWithInputs(
                mockupPath: "\(mockupFolder)/\(mockupName)",
                mockupName: mockupName,
                assignedInputFiles: [] // pusta lista = użyj wszystkich (fallback w silniku)
            ))
        }
        
        return mockups
    }
    
    // MARK: - Build JSX Content
    
    private static func buildJSXContent(
        mockupsConfig: [MockupWithInputs],
        inputFolder: String,
        outputFolder: String,
        smartObjectName: String,
        outputFormat: String,
        alignment: String,
        resizeMode: String,
        enginePath: String
    ) -> String {
        
        var jsx = ""
        
        // Header
        jsx += "// Generated by Smart Mockup Creator\n"
        jsx += "// Date: \(Date())\n"
        jsx += "// Engine path: \(enginePath)\n\n"
        jsx += "#include \"\(enginePath)\"\n\n"
        
        // Debug logging
        jsx += generateDebugLoggingFunction()
        
        // Validate engine
        jsx += generateEngineValidation(enginePath: enginePath)
        
        // Output options
        jsx += "\nvar outputOpts = {\n"
        jsx += "  path: '\(outputFolder)',\n"
        jsx += "  format: '\(outputFormat)',\n"
        jsx += "  zeroPadding: true,\n"
        jsx += "  filename: '@input_@mockup'\n"
        jsx += "};\n\n"
        
        // Mockups array
        jsx += "mockups([\n"
        
        for (index, mockup) in mockupsConfig.enumerated() {
            jsx += generateMockupObject(
                mockup: mockup,
                inputFolder: inputFolder,
                smartObjectName: smartObjectName,
                alignment: alignment,
                resizeMode: resizeMode
            )
            
            if index < mockupsConfig.count - 1 {
                jsx += ",\n\n"
            }
        }
        
        jsx += "\n]);\n\n"
        
        // Footer
        jsx += generateFooter(mockupCount: mockupsConfig.count)
        
        return jsx
    }
    
    // MARK: - Generate Mockup Object
    
    private static func generateMockupObject(
        mockup: MockupWithInputs,
        inputFolder: String,
        smartObjectName: String,
        alignment: String,
        resizeMode: String
    ) -> String {
        
        var jsx = "  {\n"
        jsx += "    output: outputOpts,\n"
        jsx += "    mockupPath: '\(mockup.mockupPath)',\n"
        jsx += "    smartObjects: [\n"
        jsx += "      {\n"
        jsx += "        target: '\(smartObjectName)',\n"
        jsx += "        input: '\(inputFolder)',\n"
        
        // *** KLUCZOWA ZMIANA: Dodaj inputFiles jeśli istnieją ***
        if !mockup.assignedInputFiles.isEmpty {
            jsx += "        inputFiles: ["
            jsx += mockup.assignedInputFiles.map { "'\($0)'" }.joined(separator: ", ")
            jsx += "],\n"
        }
        
        jsx += "        align: '\(alignment)',\n"
        jsx += "        resize: '\(resizeMode)'\n"
        jsx += "      }\n"
        jsx += "    ]\n"
        jsx += "  }"
        
        return jsx
    }
    
    // MARK: - Helper Functions
    
    private static func generateDebugLoggingFunction() -> String {
        return """
        // Debug logging function
        function logDebug(message) {
          try {
            var logFile = new File(Folder.desktop + '/mockup_generator_debug.log');
            logFile.open('a');
            logFile.writeln(new Date().toString() + ': ' + message);
            logFile.close();
          } catch(e) {
            // Silent fail for logging
          }
        }
        
        
        """
    }
    
    private static func generateEngineValidation(enginePath: String) -> String {
        return """
        // Validate engine file exists
        try {
          var engineFile = new File('\(enginePath)');
          if (!engineFile.exists) {
            alert('ERROR: Engine file not found!\\n\\nExpected location:\\n\(enginePath)\\n\\nPlease check if the file exists at this path.');
            logDebug('ERROR: Engine file not found at: \(enginePath)');
            throw new Error('Engine file not found');
          }
          logDebug('Engine file found at: \(enginePath)');
        } catch(e) {
          alert('Critical Error: ' + e.toString());
          throw e;
        }
        
        
        """
    }
    
    private static func generateFooter(mockupCount: Int) -> String {
        return """
        logDebug('Script completed successfully');
        logDebug('Files processed: \(mockupCount) mockup(s)');
        alert('Batch process completed!\\nProcessed: \(mockupCount) mockup(s)\\nCheck Desktop for debug log if issues occur.');
        
        // Script completed successfully
        // Files processed: \(mockupCount) mockup(s)
        """
    }
}
```

---

### CZĘŚĆ B: Skrypt Silnika (ExtendScript)

#### Krok 4: Modyfikacja `prepFiles()` w silniku (1 godzina)

**Plik:** `Batch Mockup Smart Object Replacement.jsx`  
**Lokalizacja:** Linia ~310

**Obecna implementacja:**
```javascript
function prepFiles( item, data ) {
  
  if ( typeof item.input === 'string' ) item.input = [ item.input ];
  
  var inputFiles = [];
  for ( var i=0; i < item.input.length; i++ ) {
    var inputFolder = new Folder( item.input[i] );
    var files = getFiles( inputFolder, item, data );
    if ( files ) inputFiles = inputFiles.concat( files );
  };
  
  return inputFiles.sort(function (a, b) {
    if ( app.compareWithNumbers ) {
      return app.compareWithNumbers(a.name, b.name)
    }
    else {
      return sortAlphaNum(a.name, b.name);
    }
  });
  
}
```

**Nowa implementacja z obsługą `inputFiles`:**
```javascript
function prepFiles( item, data ) {
  
  // *** NOWA FUNKCJA: Sprawdź czy item ma zdefiniowane inputFiles ***
  if ( item.inputFiles && item.inputFiles.length > 0 ) {
    return filterFilesByNames( item.input, item.inputFiles );
  }
  
  // STARA LOGIKA: Jeśli nie ma inputFiles, zwróć wszystkie pliki
  if ( typeof item.input === 'string' ) item.input = [ item.input ];
  
  var inputFiles = [];
  for ( var i=0; i < item.input.length; i++ ) {
    var inputFolder = new Folder( item.input[i] );
    var files = getFiles( inputFolder, item, data );
    if ( files ) inputFiles = inputFiles.concat( files );
  };
  
  return inputFiles.sort(function (a, b) {
    if ( app.compareWithNumbers ) {
      return app.compareWithNumbers(a.name, b.name)
    }
    else {
      return sortAlphaNum(a.name, b.name);
    }
  });
  
}
```

---

#### Krok 5: Dodaj funkcję `filterFilesByNames()` (30 min)

**Plik:** `Batch Mockup Smart Object Replacement.jsx`  
**Miejsce:** Po funkcji `prepFiles()`

```javascript
/**
 * Filter files from folder by specific filenames
 * @param {string|array} inputPath - Path to input folder(s)
 * @param {array} fileNames - Array of filenames to include (e.g., ['1.jpeg', '3.jpeg'])
 * @return {array} - Array of File objects matching the names
 */
function filterFilesByNames( inputPath, fileNames ) {
  
  if ( typeof inputPath === 'string' ) inputPath = [ inputPath ];
  
  var filteredFiles = [];
  
  // Dla każdego folderu input
  for ( var i=0; i < inputPath.length; i++ ) {
    var inputFolder = new Folder( inputPath[i] );
    
    if ( !inputFolder.exists ) continue;
    
    // Dla każdej nazwy pliku z listy
    for ( var j=0; j < fileNames.length; j++ ) {
      var fileName = fileNames[j];
      var filePath = inputFolder.fsName + '/' + fileName;
      var file = new File( filePath );
      
      if ( file.exists ) {
        filteredFiles.push( file );
      } else {
        alert('Warning: File not found: ' + fileName + '\nExpected at: ' + filePath);
      }
    }
  }
  
  // Sortuj wyniki
  return filteredFiles.sort(function (a, b) {
    if ( app.compareWithNumbers ) {
      return app.compareWithNumbers(a.name, b.name)
    }
    else {
      return sortAlphaNum(a.name, b.name);
    }
  });
  
}
```

---

### CZĘŚĆ C: UI i UX (opcjonalne, 2-4 godziny)

#### Krok 6: Dodaj podgląd kombinacji w UI

**Plik:** Nowy `ConfigPreviewView.swift`

```swift
import SwiftUI

struct ConfigPreviewView: View {
    let mockupsConfig: [MockupWithInputs]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Preview: Combinations from config.json")
                .font(.headline)
            
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(mockupsConfig, id: \.mockupName) { mockup in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(mockup.mockupName)
                                .font(.subheadline)
                                .fontWeight(.semibold)
                            
                            ForEach(mockup.assignedInputFiles, id: \.self) { inputFile in
                                HStack {
                                    Image(systemName: "arrow.right")
                                        .foregroundColor(.blue)
                                    Text(inputFile)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .padding(.leading, 16)
                            }
                        }
                        .padding(.vertical, 4)
                        
                        Divider()
                    }
                }
            }
            
            HStack {
                Text("Total combinations:")
                    .font(.footnote)
                Spacer()
                Text("\(totalCombinations)")
                    .font(.footnote)
                    .fontWeight(.bold)
            }
        }
        .padding()
        .frame(maxWidth: 400, maxHeight: 300)
    }
    
    private var totalCombinations: Int {
        mockupsConfig.reduce(0) { $0 + $1.assignedInputFiles.count }
    }
}
```

#### Krok 7: Integracja z głównym widokiem

**Plik:** `MockupGeneratorView.swift`

```swift
struct MockupGeneratorView: View {
    @State private var showPreview = false
    @State private var mockupsConfig: [MockupWithInputs] = []
    
    // ... reszta kodu ...
    
    var body: some View {
        VStack {
            // ... istniejące UI ...
            
            // Przycisk podglądu
            Button("Preview Combinations") {
                loadConfigPreview()
                showPreview = true
            }
            .disabled(configPath == nil || configPath!.isEmpty)
            
            // ... reszta kodu ...
        }
        .sheet(isPresented: $showPreview) {
            ConfigPreviewView(mockupsConfig: mockupsConfig)
        }
    }
    
    private func loadConfigPreview() {
        guard let configPath = configPath,
              !configPath.isEmpty,
              !inputFolder.isEmpty,
              !mockupFolder.isEmpty else {
            return
        }
        
        do {
            let config = try ConfigService.loadConfig(from: configPath)
            mockupsConfig = try ConfigService.buildMockupMapping(
                config: config,
                inputFolder: inputFolder,
                mockupFolder: mockupFolder
            )
        } catch {
            print("Error loading preview: \(error)")
        }
    }
}
```

---

## Przykład Wygenerowanego JSX

### Input:
**config.json:**
```json
{
  "1.jpeg": ["1.psd", "2.psd"],
  "2.jpeg": ["2.psd", "3.psd"],
  "3.jpeg": ["1.psd", "3.psd"]
}
```

### Output:
**main_mockup_generator.jsx:**
```javascript
// Generated by Smart Mockup Creator
// Date: 2025-10-30 15:46:52

#include "/path/to/engine/Batch Mockup Smart Object Replacement.jsx"

function logDebug(message) { /* ... */ }

var outputOpts = {
  path: '/path/to/output',
  format: 'jpg',
  zeroPadding: true,
  filename: '@input_@mockup'
};

mockups([
  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/1.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',
        inputFiles: ['1.jpeg', '3.jpeg'],    // ← FILTROWANIE
        align: 'center center',
        resize: 'fill'
      }
    ]
  },

  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/2.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',
        inputFiles: ['1.jpeg', '2.jpeg'],    // ← FILTROWANIE
        align: 'center center',
        resize: 'fill'
      }
    ]
  },

  {
    output: outputOpts,
    mockupPath: '/path/to/mockup/3.psd',
    smartObjects: [
      {
        target: 'Frame 1',
        input: '/path/to/input',
        inputFiles: ['2.jpeg', '3.jpeg'],    // ← FILTROWANIE
        align: 'center center',
        resize: 'fill'
      }
    ]
  }
]);

alert('Batch process completed!');
```

---

## Testowanie

### Test 1: Z config.json (podstawowy)
**Setup:**
- config.json jak powyżej
- 3 pliki input, 3 pliki mockup

**Kroki:**
1. Uruchom aplikację macOS
2. Wybierz foldery i config.json
3. Kliknij "Preview Combinations"
4. Sprawdź czy pokazuje 6 kombinacji
5. Wygeneruj skrypt
6. Uruchom w Photoshop

**Oczekiwany rezultat:**
- 6 plików wyjściowych
- Nazwy: `1_1.jpg`, `1_2.jpg`, `2_2.jpg`, `2_3.jpg`, `3_1.jpg`, `3_3.jpg`

### Test 2: Bez config.json (fallback)
**Setup:**
- Brak config.json lub puste pole w UI

**Oczekiwany rezultat:**
- Stara logika: 9 plików (każdy input na każdy mockup)
- Brak błędów

### Test 3: Z błędami w config
**Setup:**
- config.json zawiera nieistniejący plik

**Oczekiwany rezultat:**
- Warnings w konsoli
- Pomija nieistniejące kombinacje
- Przetwarza pozostałe

### Test 4: Wielokrotne użycie tego samego input
**config.json:**
```json
{
  "1.jpeg": ["1.psd", "2.psd", "3.psd"]
}
```

**Oczekiwany rezultat:**
- 3 pliki wyjściowe (wszystkie z 1.jpeg)

---

## Porównanie z innymi hipotezami

### Wydajność (czas wykonania)

| Scenariusz | Hipoteza 1 | Hipoteza 2 | Hipoteza 3 |
|------------|------------|------------|------------|
| 3 mockupy, 3 input, 6 kombinacji | ~12-18s | ~6-9s | ~6-9s |
| 20 mockupów, 100 input, 500 kombinacji | ~16-25min | ~40-60s | ~40-60s |

**Zwycięzca: Hipoteza 2 i 3 (remis)**

### Złożoność implementacji

| Aspekt | Hipoteza 1 | Hipoteza 2 | Hipoteza 3 |
|--------|------------|------------|------------|
| Zmiany w aplikacji | Średnie | Brak | Duże |
| Zmiany w silniku | Brak | Duże | Małe |
| Trudność testowania | Łatwe | Trudne | Średnie |
| Czas implementacji | 9-13h | 9-13h | 12-16h |

**Zwycięzca: Hipoteza 1 (najprostsza)**

### Elastyczność i przyszłość

| Feature | Hipoteza 1 | Hipoteza 2 | Hipoteza 3 |
|---------|------------|------------|------------|
| UI preview | Trudne | Trudne | Łatwe ✅ |
| Walidacja | Średnia | Trudna | Łatwa ✅ |
| Error handling | Średnie | Trudne | Łatwe ✅ |
| Rozszerzalność | Trudne | Średnie | Łatwe ✅ |

**Zwycięzca: Hipoteza 3**

---

## Harmonogram Implementacji

### Tydzień 1: Aplikacja macOS
**Dzień 1-2 (6-8h):**
- [ ] Struktury danych
- [ ] ConfigService - load, parse, validate
- [ ] Testy jednostkowe ConfigService

**Dzień 3-4 (6-8h):**
- [ ] Modyfikacja JSXGeneratorService
- [ ] Generowanie inputFiles w JSX
- [ ] Testy generatora

### Tydzień 2: Skrypt Silnika
**Dzień 5 (3-4h):**
- [ ] Backup silnika
- [ ] Modyfikacja prepFiles()
- [ ] Dodanie filterFilesByNames()

**Dzień 6 (3-4h):**
- [ ] Testy integracyjne end-to-end
- [ ] Testy fallback (bez config)
- [ ] Testy edge cases

### Tydzień 3: UI i Finalizacja (opcjonalnie)
**Dzień 7-8 (6-8h):**
- [ ] ConfigPreviewView
- [ ] Integracja z głównym UI
- [ ] Walidacja w UI

**Dzień 9 (2-3h):**
- [ ] Dokumentacja
- [ ] Cleanup kodu
- [ ] Final testing

**Szacowany czas całkowity: 12-16 godzin (core) + 8-11 godzin (UI)**

---

## Plusy i minusy w produkcji

### ✅ Zalecane dla:
- Projektów gdzie UI/UX jest ważne
- Zespołów z większą wiedzą Swift niż JSX
- Długoterminowych projektów (więcej feature'ów w przyszłości)
- Sytuacji gdzie potrzebny jest podgląd przed wykonaniem

### ❌ Nie zalecane dla:
- Bardzo prostych use case'ów (overkill)
- Projektów gdzie nie chce się modyfikować silnika (użyj Hipotezy 1)
- Sytuacji gdzie priorytetem jest szybkość implementacji

---

## Przyszłe rozszerzenia (roadmap)

### Faza 1 (MVP) - już opisana wyżej
- ✅ Podstawowe filtrowanie z config.json
- ✅ Preview kombinacji

### Faza 2 - Zaawansowane funkcje
- [ ] UI do tworzenia/edycji config.json
- [ ] Drag & drop przypisywania input → mockup
- [ ] Walidacja "na żywo" podczas edycji
- [ ] Export/import różnych konfiguracji

### Faza 3 - Optymalizacje
- [ ] Grupowanie mockupów (zmniejszenie otworzeń)
- [ ] Priorytetyzacja kolejności przetwarzania
- [ ] Parallel processing (jeśli Photoshop pozwala)
- [ ] Incremental builds (tylko zmienione pliki)

### Faza 4 - Integracje
- [ ] Integracja z systemami DAM
- [ ] API do automatyzacji
- [ ] Webhook po zakończeniu
- [ ] Cloud storage support

---

## Migracja między hipotezami

### Z Hipotezy 1 do 3:
1. Przywróć aplikację do wersji sprzed zmian
2. Zaimplementuj ConfigService (nowy kod)
3. Zmodyfikuj generator JSX (dodaj inputFiles)
4. Dodaj filterFilesByNames() do silnika
5. Przetestuj

### Z Hipotezy 2 do 3:
1. Usuń config parsing z silnika
2. Przenieś logikę do aplikacji Swift
3. Zmień API silnika (inputFiles zamiast configFilter)
4. Przetestuj

---

## Checklist przed rozpoczęciem

### Przygotowanie środowiska
- [ ] Backup aplikacji i silnika
- [ ] Środowisko testowe
- [ ] Git repository
- [ ] Xcode i Swift 5.5+
- [ ] Photoshop CC 2019+

### Wiedza wymagana
- [ ] Swift basics
- [ ] SwiftUI (jeśli UI)
- [ ] JSON parsing w Swift
- [ ] ExtendScript/JSX basics
- [ ] Photoshop scripting

### Zrozumienie
- [ ] Obecny przepływ aplikacji
- [ ] Format config.json
- [ ] API skryptu silnika
- [ ] Proces generowania JSX

---

## Rekomendacja Finalna

### Wybierz Hipotezę 3 jeśli:
✅ Planujesz dodawać więcej funkcji w przyszłości  
✅ Chcesz mieć preview przed wykonaniem  
✅ Preferujesz Swift nad JSX  
✅ Performance jest ważne (duże projekty)  
✅ Masz czas na implementację UI (12-16h + UI)

### Wybierz Hipotezę 2 jeśli:
✅ Performance jest NAJWAŻNIEJSZE  
✅ NIE chcesz modyfikować aplikacji  
✅ Jesteś komfortowy z JSX/ExtendScript  
✅ Nie potrzebujesz UI preview

### Wybierz Hipotezę 1 jeśli:
✅ Chcesz najszybszą implementację (9-13h)  
✅ Mały projekt (< 20 plików)  
✅ NIE chcesz modyfikować silnika  
✅ Prostota > Performance

---

## Podsumowanie implementacji

### Co trzeba zrobić:

**Aplikacja macOS (Swift):**
1. Stwórz `ConfigService.swift`
2. Dodaj metody: `loadConfig()`, `buildMockupMapping()`, `validateConfig()`
3. Modyfikuj `JSXGeneratorService.swift` - dodaj generowanie `inputFiles`
4. (Opcjonalnie) Dodaj `ConfigPreviewView.swift`

**Skrypt Silnika (JSX):**
1. Modyfikuj `prepFiles()` - sprawdź `item.inputFiles`
2. Dodaj `filterFilesByNames()` - filtruj pliki według nazw

**Testowanie:**
1. Test z config.json
2. Test bez config.json (fallback)
3. Test z błędami
4. Performance test

---

*Dokument stworzony: 2025-10-30*
*Wersja: 1.0*
*Zalecana dla: Średnich i dużych projektów z planami rozwoju*
