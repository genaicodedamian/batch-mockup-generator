# Plan Implementacji - Hipoteza 2: Modyfikacja Skryptu Silnika

## Podsumowanie
Najbardziej wydajne rozwiązanie - modyfikacja skryptu silnika JSX, aby filtrował pliki input według `config.json`. Każdy mockup PSD jest otwierany tylko raz i przetwarza tylko przypisane mu pliki.

---

## Zalety ✅
- ✅ **Maksymalna wydajność** - każdy mockup otwierany tylko RAZ
- ✅ **Skalowalność** - świetne dla dużych projektów (100+ plików)
- ✅ **Mniejsze zużycie zasobów** - mniej operacji I/O, mniej pamięci
- ✅ **Czystszy output JSX** - tylko 3 obiekty mockup (jak teraz)
- ✅ **Eleganckie rozwiązanie** - logika w odpowiednim miejscu
- ✅ **Elastyczność** - łatwo dodać nowe funkcje filtrowania

## Wady ❌
- ❌ **Modyfikacja skryptu silnika** - ryzyko złamania istniejącej funkcjonalności
- ❌ **Bardziej skomplikowana implementacja** - zmiany w JSX (ExtendScript)
- ❌ **Trudniejsze testowanie** - ExtendScript ma ograniczone narzędzia
- ❌ **Kompatybilność wstecz** - trzeba zachować starą logikę jako fallback
- ❌ **Debugowanie** - JSX trudniej debugować niż Swift

---

## Analiza Problemu

### Obecny przepływ (uproszczony):
```
1. Otwórz mockup 1.psd
2. prepFiles() → zwróć WSZYSTKIE pliki z input/
3. replaceLoop() → iteruj przez WSZYSTKIE pliki
4. Zapisz output dla każdego pliku
5. Zamknij mockup 1.psd

6. Otwórz mockup 2.psd
7. prepFiles() → zwróć WSZYSTKIE pliki z input/
8. replaceLoop() → iteruj przez WSZYSTKIE pliki
9. Zapisz output dla każdego pliku
10. Zamknij mockup 2.psd

... itd.
```

### Docelowy przepływ:
```
1. Wczytaj config.json
2. Otwórz mockup 1.psd
3. prepFiles() → zwróć TYLKO pliki przypisane do 1.psd
4. replaceLoop() → iteruj przez TYLKO te pliki
5. Zapisz output dla każdego pliku
6. Zamknij mockup 1.psd

7. Otwórz mockup 2.psd
8. prepFiles() → zwróć TYLKO pliki przypisane do 2.psd
9. replaceLoop() → iteruj przez TYLKO te pliki
10. Zapisz output dla każdego pliku
11. Zamknij mockup 2.psd

... itd.
```

---

## Kluczowe Zmiany w Skrypcie Silnika

### Zmiana 1: Dodanie obsługi config.json

**Lokalizacja:** Na początku pliku `Batch Mockup Smart Object Replacement.jsx`

```javascript
// NOWA FUNKCJA: Wczytanie config.json
function loadConfigMapping(configPath) {
  try {
    var configFile = new File(configPath);
    
    if (!configFile.exists) {
      return null; // Fallback do starej logiki
    }
    
    configFile.open('r');
    var content = configFile.read();
    configFile.close();
    
    // Parse JSON (używamy wbudowanej biblioteki JSON)
    var config = JSON.parse(content);
    
    return config;
    
  } catch(e) {
    alert('Error loading config.json: ' + e.toString());
    return null;
  }
}

// NOWA FUNKCJA: Konwersja config do mapy mockup → [input files]
function buildMockupToInputMap(config, mockupPath, inputFolder) {
  var map = {}; // { 'mockup/1.psd': ['input/1.jpeg', 'input/3.jpeg'] }
  
  if (!config) return null;
  
  // Pobierz nazwę mockupa z pełnej ścieżki
  var mockupFile = new File(mockupPath);
  var mockupName = mockupFile.name; // np. "1.psd"
  
  // Iteruj przez config
  for (var inputKey in config) {
    if (!config.hasOwnProperty(inputKey)) continue;
    
    var mockupList = config[inputKey]; // tablica np. ["1.psd", "2.psd"]
    
    // Sprawdź czy ten mockup jest w liście
    for (var i = 0; i < mockupList.length; i++) {
      if (mockupList[i] === mockupName) {
        
        // Znajdź faktyczny plik w folderze input
        var actualInputFile = findActualInputFile(inputKey, inputFolder);
        
        if (actualInputFile) {
          if (!map[mockupName]) map[mockupName] = [];
          map[mockupName].push(actualInputFile);
        }
        
      }
    }
  }
  
  return map[mockupName] || [];
}

// NOWA FUNKCJA: Znajdź faktyczny plik w folderze
function findActualInputFile(configKey, inputFolder) {
  // configKey może być "1.png", faktyczny plik to "1.jpeg"
  
  // Usuń rozszerzenie z klucza
  var baseName = configKey.replace(/\.[^.]+$/, '');
  
  var folder = new Folder(inputFolder);
  var files = folder.getFiles();
  
  for (var i = 0; i < files.length; i++) {
    if (files[i] instanceof Folder) continue;
    
    var fileName = files[i].name;
    var fileBase = fileName.replace(/\.[^.]+$/, '');
    
    if (fileBase === baseName) {
      return files[i]; // Zwróć obiekt File
    }
  }
  
  return null;
}
```

---

### Zmiana 2: Modyfikacja funkcji `prepFiles()`

**Lokalizacja:** Linia ~310 w `Batch Mockup Smart Object Replacement.jsx`

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

**Nowa implementacja z filtrowaniem:**
```javascript
function prepFiles( item, data ) {
  
  // NOWE: Sprawdź czy mamy config filtering dla tego mockupa
  if (data.configFilter && data.configFilter.length > 0) {
    // Zwróć tylko pliki z config
    return data.configFilter.sort(function (a, b) {
      if ( app.compareWithNumbers ) {
        return app.compareWithNumbers(a.name, b.name)
      }
      else {
        return sortAlphaNum(a.name, b.name);
      }
    });
  }
  
  // STARA LOGIKA: Jeśli nie ma config, zwróć wszystkie pliki (fallback)
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

### Zmiana 3: Modyfikacja funkcji `soReplaceBatch()`

**Lokalizacja:** Linia ~116 w `Batch Mockup Smart Object Replacement.jsx`

**Obecna implementacja:**
```javascript
function soReplaceBatch( mockups ) {
  
  addMultipleMockupsByPath( mockups );
  
  each( mockups, function( mockup ) {
    // ... iteracja przez mockupy
  });
  
  alert('Batch process done!');
}
```

**Nowa implementacja z config:**
```javascript
function soReplaceBatch( mockups ) {
  
  addMultipleMockupsByPath( mockups );
  
  // NOWE: Sprawdź czy istnieje config.json
  var configPath = null;
  var configMapping = null;
  
  // Spróbuj znaleźć config.json w różnych lokacjach
  var possiblePaths = [
    includePath + '/config.json',           // Obok skryptu settings
    docPath + '/config.json',                // W folderze projektu
    '$/config.json'                          // Relatywna ścieżka
  ];
  
  for (var i = 0; i < possiblePaths.length; i++) {
    var testPath = absolutelyRelativePath(possiblePaths[i]);
    if (testPath.file && testPath.file.exists) {
      configPath = testPath.file.fsName;
      break;
    }
  }
  
  // Wczytaj config jeśli znaleziono
  if (configPath) {
    configMapping = loadConfigMapping(configPath);
    if (configMapping) {
      alert('Config.json loaded successfully!\nFiltering enabled.');
    }
  }
  
  each( mockups, function( mockup ) {
    
    // Don't process this mockup
    if ( mockup.ignore ) return;
    
    var mockupPSD = absolutelyRelativePath( mockup.mockupPath );
    if ( mockupPSD.file && mockupPSD.extension ) {
      
      app.open( mockupPSD.file );
      
      // NOWE: Przygotuj filtr dla tego mockupa
      mockup.configFilter = null;
      if (configMapping && mockup.smartObjects && mockup.smartObjects[0]) {
        var inputFolder = absolutelyRelativePath(mockup.smartObjects[0].input);
        if (inputFolder.file) {
          mockup.configFilter = buildMockupToInputMap(
            configMapping,
            mockupPSD.file.fsName,
            inputFolder.file.fsName
          );
        }
      }
      
      if ( mockup.showLayers ) {
        each( mockup.showLayers, function( layerName ) {
          var layer = getLayer( layerName );
          layer.visible = true;
        });
      }
      
      if ( mockup.hideLayers ) {
        each( mockup.hideLayers, function( layerName ) {
          var layer = getLayer( layerName );
          layer.visible = false;
        });
      }
      
      mockup.items = mockup.smartObjects;
      delete mockup.smartObjects;
      
      soReplace( mockup );
      
      app.activeDocument.close( SaveOptions.DONOTSAVECHANGES );
      
    }
  
  });
  
  alert('Batch process done!');
}
```

---

### Zmiana 4: Przekazanie configFilter do funkcji init()

**Lokalizacja:** Funkcja `soReplace()` i `init()`, linia ~195

**Modyfikacja `soReplace()`:**
```javascript
function soReplace( rawData ) {
  
  app.activeDocument.suspendHistory("soReplace", "init(rawData)");
  
  function init( rawData ) {
    
    var rulerUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;
    
    var data = replaceLoopOptionsFiller( rawData );
    
    // NOWE: Przekaż configFilter do data
    data.configFilter = rawData.configFilter || null;
    
    // Preparing files
    if ( data.doc.input ) {
      
      data.doc.files = prepFiles( data.doc, data );
      data.maxLoop = Math.ceil(data.doc.files.length / data.items.length);
      data.largestArray = data.doc.files;
      
    }
    else {
      
      each( data.items, function( item ) {
        item.files = prepFiles( item, data ); // ← data zawiera teraz configFilter
      });
      
      // This makes sure all file arrays are the same length
      data = evenOutFileArrays( data );
      
    }
    
    replaceLoop( data );
    
    app.preferences.rulerUnits = rulerUnits;
    
  }
  
}
```

---

## Szczegółowy Plan Implementacji

### Faza 1: Backup i przygotowanie (30 min)
1. ✅ **Backup skryptu silnika**
   ```bash
   cp "Batch Mockup Smart Object Replacement.jsx" \
      "Batch Mockup Smart Object Replacement.jsx.backup"
   ```

2. ✅ **Stwórz środowisko testowe**
   ```
   test-config-filtering/
   ├── config.json
   ├── input/
   │   ├── 1.jpeg
   │   ├── 2.jpeg
   │   └── 3.jpeg
   ├── mockup/
   │   ├── 1.psd
   │   ├── 2.psd
   │   └── 3.psd
   └── test-script.jsx
   ```

3. ✅ **Przygotuj test-script.jsx**
   ```javascript
   #include "../script/Batch Mockup Smart Object Replacement.jsx"
   
   var outputOpts = {
     path: '$/output',
     format: 'jpg',
     filename: '@input_@mockup'
   };
   
   mockups([
     {
       output: outputOpts,
       mockupPath: '$/mockup/1.psd',
       smartObjects: [
         { target: 'Frame 1', input: '$/input', align: 'center center', resize: 'fill' }
       ]
     },
     {
       output: outputOpts,
       mockupPath: '$/mockup/2.psd',
       smartObjects: [
         { target: 'Frame 1', input: '$/input', align: 'center center', resize: 'fill' }
       ]
     },
     {
       output: outputOpts,
       mockupPath: '$/mockup/3.psd',
       smartObjects: [
         { target: 'Frame 1', input: '$/input', align: 'center center', resize: 'fill' }
       ]
     }
   ]);
   ```

---

### Faza 2: Implementacja funkcji pomocniczych (2-3 godziny)

#### Krok 1: Dodaj funkcję `loadConfigMapping()`
**Plik:** `Batch Mockup Smart Object Replacement.jsx`  
**Miejsce:** Po linii ~115 (przed `function soReplaceBatch()`)

```javascript
// ============================================================================
// CONFIG.JSON SUPPORT
// ============================================================================

/**
 * Load and parse config.json file
 * @param {string} configPath - Absolute path to config.json
 * @return {Object|null} - Parsed config or null if error
 */
function loadConfigMapping(configPath) {
  try {
    var configFile = new File(configPath);
    
    if (!configFile.exists) {
      return null;
    }
    
    configFile.open('r');
    var content = configFile.read();
    configFile.close();
    
    // Parse JSON
    var config = JSON.parse(content);
    
    // Validate basic structure
    if (typeof config !== 'object' || config === null) {
      throw new Error('Invalid config format');
    }
    
    return config;
    
  } catch(e) {
    alert('Error loading config.json: ' + e.toString());
    return null;
  }
}
```

#### Krok 2: Dodaj funkcję `findActualInputFile()`
```javascript
/**
 * Find actual file in folder matching config key
 * @param {string} configKey - Key from config.json (e.g., "1.png")
 * @param {string} inputFolderPath - Path to input folder
 * @return {File|null} - File object or null
 */
function findActualInputFile(configKey, inputFolderPath) {
  // Remove extension from key
  var baseName = configKey.replace(/\.[^.]+$/, '');
  
  var folder = new Folder(inputFolderPath);
  
  if (!folder.exists) {
    return null;
  }
  
  var files = folder.getFiles();
  
  for (var i = 0; i < files.length; i++) {
    if (files[i] instanceof Folder) continue;
    
    var fileName = files[i].name;
    var fileBase = fileName.replace(/\.[^.]+$/, '');
    
    if (fileBase.toLowerCase() === baseName.toLowerCase()) {
      return files[i];
    }
  }
  
  return null;
}
```

#### Krok 3: Dodaj funkcję `buildMockupToInputMap()`
```javascript
/**
 * Build list of input files for specific mockup based on config
 * @param {Object} config - Parsed config.json
 * @param {string} mockupPath - Path to mockup PSD
 * @param {string} inputFolderPath - Path to input folder
 * @return {Array} - Array of File objects
 */
function buildMockupToInputMap(config, mockupPath, inputFolderPath) {
  var inputFiles = [];
  
  if (!config) return inputFiles;
  
  // Get mockup filename
  var mockupFile = new File(mockupPath);
  var mockupName = mockupFile.name;
  
  // Iterate through config
  for (var inputKey in config) {
    if (!config.hasOwnProperty(inputKey)) continue;
    
    var mockupList = config[inputKey]; // Array like ["1.psd", "2.psd"]
    
    if (!(mockupList instanceof Array)) continue;
    
    // Check if this mockup is in the list
    for (var i = 0; i < mockupList.length; i++) {
      if (mockupList[i] === mockupName) {
        
        // Find actual file in input folder
        var actualFile = findActualInputFile(inputKey, inputFolderPath);
        
        if (actualFile) {
          // Check if not already added (avoid duplicates)
          var alreadyAdded = false;
          for (var j = 0; j < inputFiles.length; j++) {
            if (inputFiles[j].fsName === actualFile.fsName) {
              alreadyAdded = true;
              break;
            }
          }
          
          if (!alreadyAdded) {
            inputFiles.push(actualFile);
          }
        } else {
          alert('Warning: Input file not found for key "' + inputKey + '"');
        }
        
      }
    }
  }
  
  return inputFiles;
}
```

---

### Faza 3: Modyfikacja głównych funkcji (2-3 godziny)

#### Krok 4: Modyfikuj `soReplaceBatch()`
**Znajdź:** Linię ~116  
**Zastąp:** Całą funkcję zgodnie z kodem pokazanym w sekcji "Zmiana 3" powyżej

#### Krok 5: Modyfikuj `prepFiles()`
**Znajdź:** Linię ~310  
**Zastąp:** Całą funkcję zgodnie z kodem pokazanym w sekcji "Zmiana 2" powyżej

#### Krok 6: Modyfikuj `soReplace()` → `init()`
**Znajdź:** Linię ~195-230  
**Dodaj:** Linię przekazującą `configFilter` zgodnie z sekcją "Zmiana 4" powyżej

---

### Faza 4: Testowanie (3-4 godziny)

#### Test 1: Z config.json
1. Stwórz `config.json`:
   ```json
   {
     "1.jpeg": ["1.psd", "2.psd"],
     "2.jpeg": ["2.psd", "3.psd"],
     "3.jpeg": ["1.psd", "3.psd"]
   }
   ```

2. Uruchom skrypt w Photoshop

3. **Oczekiwany rezultat:**
   - Mockup 1.psd: przetworzy tylko 1.jpeg i 3.jpeg (2 pliki)
   - Mockup 2.psd: przetworzy tylko 1.jpeg i 2.jpeg (2 pliki)
   - Mockup 3.psd: przetworzy tylko 2.jpeg i 3.jpeg (2 pliki)
   - **Razem: 6 plików wyjściowych**

4. **Sprawdź:**
   - Czy utworzono dokładnie 6 plików?
   - Czy nazwy są poprawne?
   - Czy kombinacje są zgodne z config.json?

#### Test 2: Bez config.json (fallback)
1. Usuń lub zmień nazwę `config.json`

2. Uruchom skrypt w Photoshop

3. **Oczekiwany rezultat:**
   - Stara logika: każdy mockup przetwarza wszystkie pliki input
   - **Razem: 9 plików wyjściowych**

4. **Sprawdź:**
   - Czy działa jak poprzednio?
   - Czy brak config.json nie powoduje błędów?

#### Test 3: Niepoprawny config.json
1. Stwórz niepoprawny JSON:
   ```json
   {
     "1.jpeg": ["1.psd", "2.psd"
   }
   ```

2. Uruchom skrypt

3. **Oczekiwany rezultat:**
   - Alert z błędem parsowania
   - Fallback do starej logiki

#### Test 4: Nieistniejące pliki w config
1. Config z nieistniejącym plikiem:
   ```json
   {
     "nonexistent.png": ["1.psd"],
     "2.jpeg": ["2.psd"]
   }
   ```

2. **Oczekiwany rezultat:**
   - Warning dla "nonexistent.png"
   - Pomija tę kombinację
   - Przetwarza tylko 2.jpeg → 2.psd

#### Test 5: Różne rozszerzenia
1. Config używa ".png", faktyczne pliki to ".jpeg":
   ```json
   {
     "1.png": ["1.psd"],
     "2.png": ["2.psd"]
   }
   ```

2. **Oczekiwany rezultat:**
   - Dopasowanie po basename (bez rozszerzenia)
   - Poprawne znalezienie 1.jpeg i 2.jpeg

---

### Faza 5: Debugowanie i logging (1-2 godziny)

#### Dodaj funkcję logowania
```javascript
/**
 * Debug logging function
 * @param {string} message - Message to log
 * @param {string} level - 'INFO', 'WARNING', 'ERROR'
 */
function logDebug(message, level) {
  level = level || 'INFO';
  
  try {
    var logFile = new File(Folder.desktop + '/config_filter_debug.log');
    logFile.open('a');
    logFile.writeln(
      new Date().toString() + ' [' + level + '] ' + message
    );
    logFile.close();
  } catch(e) {
    // Silent fail
  }
}
```

#### Dodaj logowanie w kluczowych miejscach
```javascript
// W loadConfigMapping()
logDebug('Loading config from: ' + configPath, 'INFO');
logDebug('Config loaded successfully', 'INFO');

// W buildMockupToInputMap()
logDebug('Building filter for mockup: ' + mockupName, 'INFO');
logDebug('Found ' + inputFiles.length + ' input files for ' + mockupName, 'INFO');

// W prepFiles()
if (data.configFilter && data.configFilter.length > 0) {
  logDebug('Using config filter: ' + data.configFilter.length + ' files', 'INFO');
} else {
  logDebug('No config filter, using all files', 'INFO');
}
```

---

### Faza 6: Optymalizacja (opcjonalnie, 1-2 godziny)

#### Optymalizacja 1: Cache config.json
Jeśli przetwarzasz wiele mockupów, nie wczytuj config za każdym razem:

```javascript
var globalConfigCache = null;

function getConfig(configPath) {
  if (globalConfigCache === null) {
    globalConfigCache = loadConfigMapping(configPath);
  }
  return globalConfigCache;
}
```

#### Optymalizacja 2: Walidacja config na starcie
```javascript
function validateConfig(config, inputFolder, mockupFolder) {
  var errors = [];
  var warnings = [];
  
  for (var inputKey in config) {
    if (!config.hasOwnProperty(inputKey)) continue;
    
    // Check if input file exists
    var inputFile = findActualInputFile(inputKey, inputFolder);
    if (!inputFile) {
      warnings.push('Input file not found: ' + inputKey);
    }
    
    // Check if mockup files exist
    var mockupList = config[inputKey];
    for (var i = 0; i < mockupList.length; i++) {
      var mockupPath = mockupFolder + '/' + mockupList[i];
      var mockupFile = new File(mockupPath);
      if (!mockupFile.exists) {
        warnings.push('Mockup file not found: ' + mockupList[i]);
      }
    }
  }
  
  return { errors: errors, warnings: warnings };
}
```

---

## Struktura Końcowa Skryptu Silnika

```
Batch Mockup Smart Object Replacement.jsx
│
├── [Linie 1-115] Istniejący kod
│
├── [NOWE] CONFIG.JSON SUPPORT
│   ├── loadConfigMapping()
│   ├── findActualInputFile()
│   ├── buildMockupToInputMap()
│   ├── logDebug()
│   └── validateConfig() [opcjonalnie]
│
├── [Zmodyfikowane] soReplaceBatch()
│   ├── Wczytanie config.json
│   ├── Przekazanie configFilter do mockups
│   └── Rest of existing logic
│
├── [Istniejące] soReplace() / init()
│   └── [Dodane] Przekazanie configFilter do data
│
├── [Zmodyfikowane] prepFiles()
│   ├── [NOWE] Sprawdzenie configFilter
│   ├── [NOWE] Zwrócenie filtrowanych plików
│   └── [FALLBACK] Stara logika
│
└── [Linie 330-1065] Istniejący kod bez zmian
```

---

## Kompatybilność Wstecz

### Strategia Fallback
Skrypt automatycznie wykrywa brak `config.json` i wraca do starej logiki:

```javascript
// Pseudokod
if (config.json exists && valid) {
  // Użyj nowej logiki filtrowania
  use_filtered_files();
} else {
  // Użyj starej logiki
  use_all_files();
}
```

### Zachowanie dla różnych scenariuszy

| Scenariusz | Zachowanie |
|------------|-----------|
| ✅ config.json istnieje i jest poprawny | Nowa logika (filtrowanie) |
| ❌ config.json nie istnieje | Stara logika (wszystkie pliki) |
| ❌ config.json niepoprawny (invalid JSON) | Alert + stara logika |
| ⚠️ config.json pusty `{}` | Żadne pliki nie zostaną przetworzone |
| ⚠️ config.json z nieistniejącymi plikami | Warning + pomija te kombinacje |

---

## Performance Comparison

### Przykład: 3 mockupy, 3 pliki input, config filtruje do 6 kombinacji

#### Hipoteza 1 (Modyfikacja aplikacji):
```
Otwarć PSD: 6
- 1.psd otwarty 2x (dla 1.jpeg i 3.jpeg)
- 2.psd otwarty 2x (dla 1.jpeg i 2.jpeg)
- 3.psd otwarty 2x (dla 2.jpeg i 3.jpeg)

Czas: ~12-18 sekund (2-3s na otwarcie × 6)
```

#### Hipoteza 2 (Modyfikacja silnika):
```
Otwarć PSD: 3
- 1.psd otwarty 1x (przetwarza 1.jpeg i 3.jpeg)
- 2.psd otwarty 1x (przetwarza 1.jpeg i 2.jpeg)
- 3.psd otwarty 1x (przetwarza 2.jpeg i 3.jpeg)

Czas: ~6-9 sekund (2-3s na otwarcie × 3)
```

**Oszczędność: ~50% czasu!**

### Duży projekt (realistyczny przykład)
- 100 plików input
- 20 mockupów
- Config: każdy input na 5 losowych mockupów
- **Razem: 500 kombinacji**

#### Hipoteza 1:
- Otwarć: 500
- Czas: ~16-25 minut

#### Hipoteza 2:
- Otwarć: 20
- Czas: ~40-60 sekund

**Oszczędność: ~96% czasu!**

---

## Dodatkowe Funkcje (Future Enhancements)

### 1. Wielokrotne config.json
Obsługa różnych konfiguracji dla różnych projektów:

```javascript
mockups([
  {
    mockupPath: '$/mockup/1.psd',
    configPath: '$/config-project-A.json',  // ← dedykowany config
    smartObjects: [...]
  }
]);
```

### 2. Inwersja logiki (exclude zamiast include)
```json
{
  "exclude": {
    "1.jpeg": ["3.psd"],
    "2.jpeg": ["1.psd"]
  }
}
```

### 3. Wildcards
```json
{
  "product-*.jpeg": ["mockup-1.psd", "mockup-2.psd"],
  "banner-*.png": ["banner-template.psd"]
}
```

### 4. Priorytetyzacja
```json
{
  "1.jpeg": {
    "mockups": ["1.psd", "2.psd"],
    "priority": 1
  },
  "2.jpeg": {
    "mockups": ["3.psd"],
    "priority": 2
  }
}
```

---

## Troubleshooting

### Problem: Config nie jest wczytywany
**Diagnoza:**
- Sprawdź log na Desktop: `config_filter_debug.log`
- Sprawdź czy config.json jest w odpowiednim miejscu

**Rozwiązanie:**
- Użyj absolutnej ścieżki w kodzie
- Sprawdź uprawnienia do pliku

### Problem: Nie wszystkie pliki są przetwarzane
**Diagnoza:**
- Sprawdź log: czy config został wczytany?
- Sprawdź czy nazwy plików w config.json są zgodne z faktycznymi

**Rozwiązanie:**
- Sprawdź basename (bez rozszerzenia)
- Upewnij się, że config.json jest poprawny JSON

### Problem: Duplikaty w output
**Diagnoza:**
- Sprawdź czy w config.json są duplikaty kombinacji

**Rozwiązanie:**
- Funkcja `buildMockupToInputMap()` już usuwa duplikaty
- Sprawdź log aby potwierdzić

### Problem: Błąd parsowania JSON
**Diagnoza:**
- Alert powinien pokazać szczegóły błędu
- Sprawdź czy config.json ma poprawną składnię

**Rozwiązanie:**
- Użyj JSON validator online
- Sprawdź przecinki, nawiasy, cudzysłowy

---

## Wymagania

### Photoshop:
- Adobe Photoshop CC 2019 lub nowszy
- Obsługa JSON.parse() (dostępne od CC 2014)

### Pliki:
- `config.json` w folderze projektu
- Poprawna składnia JSON
- Nazwy plików w config odpowiadające faktycznym (basename)

---

## Migracja z Hipotezy 1

Jeśli zaimplementowałeś już Hipotezę 1:

### Krok 1: Przywróć aplikację macOS
- Usuń kod generujący osobne obiekty mockup
- Przywróć starą logikę (3 obiekty mockup)

### Krok 2: Wdróż modyfikacje silnika
- Zastosuj zmiany z tego planu
- Przetestuj z tym samym config.json

### Krok 3: Porównaj wyniki
- Powinny być identyczne
- Ale znacznie szybsze!

---

## Checklist Implementacji

### Przygotowanie
- [ ] Backup skryptu silnika
- [ ] Stwórz środowisko testowe
- [ ] Przygotuj test-script.jsx
- [ ] Przygotuj config.json

### Implementacja
- [ ] Dodaj `loadConfigMapping()`
- [ ] Dodaj `findActualInputFile()`
- [ ] Dodaj `buildMockupToInputMap()`
- [ ] Modyfikuj `soReplaceBatch()`
- [ ] Modyfikuj `prepFiles()`
- [ ] Modyfikuj `soReplace()` / `init()`
- [ ] Dodaj `logDebug()`

### Testowanie
- [ ] Test z config.json
- [ ] Test bez config.json (fallback)
- [ ] Test z niepoprawnym config.json
- [ ] Test z nieistniejącymi plikami
- [ ] Test z różnymi rozszerzeniami
- [ ] Performance test (duży projekt)

### Dokumentacja
- [ ] Aktualizuj README
- [ ] Dokumentuj format config.json
- [ ] Dodaj przykłady
- [ ] Changelog

---

## Harmonogram

### Dzień 1 (4-6 godzin)
- ✅ Backup i przygotowanie
- ✅ Implementacja funkcji pomocniczych
- ✅ Podstawowe testy

### Dzień 2 (3-4 godziny)
- ✅ Modyfikacja głównych funkcji
- ✅ Testy integracyjne
- ✅ Debugowanie

### Dzień 3 (2-3 godziny)
- ✅ Optymalizacja
- ✅ Performance tests
- ✅ Dokumentacja

**Szacowany czas całkowity: 9-13 godzin**

---

## Rekomendacja

To podejście jest **najlepsze dla:**
- ✅ Średnich i dużych projektów (20+ plików)
- ✅ Powtarzalnych procesów produkcyjnych
- ✅ Sytuacji gdzie performance jest kluczowy
- ✅ Profesjonalnych workflow

**Nie zalecane dla:**
- ❌ Bardzo małych projektów (< 10 plików)
- ❌ Jednorazowych zadań
- ❌ Braku doświadczenia z ExtendScript

---

*Dokument stworzony: 2025-10-30*
*Wersja: 1.0*
