import json
import os

def check_file_completeness():
    """
    Checks for missing input and mockup files based on the config.json file.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    input_dir = os.path.join(os.path.dirname(__file__), 'input')
    mockup_dir = os.path.join(os.path.dirname(__file__), 'mockup')

    # 1. Load config.json and create lists of expected files
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"BŁĄD: Plik konfiguracyjny nie został znaleziony w ścieżce: {config_path}")
        return
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik konfiguracyjny {config_path} jest uszkodzony lub niepoprawnie sformatowany.")
        return

    expected_input_files = set(config_data.keys())
    
    expected_mockup_files = set()
    for mockup_list in config_data.values():
        if isinstance(mockup_list, list):
            for mockup_file in mockup_list:
                expected_mockup_files.add(mockup_file)

    # 2. Get lists of actual files from directories
    try:
        actual_input_files = set(os.listdir(input_dir))
    except FileNotFoundError:
        print(f"BŁĄD: Folder 'input' nie został znaleziony w ścieżce: {input_dir}")
        actual_input_files = set()

    try:
        actual_mockup_files = set(os.listdir(mockup_dir))
    except FileNotFoundError:
        print(f"BŁĄD: Folder 'mockup' nie został znaleziony w ścieżce: {mockup_dir}")
        actual_mockup_files = set()

    # 3. Compare lists and find missing files
    missing_input_files = expected_input_files - actual_input_files
    missing_mockup_files = expected_mockup_files - actual_mockup_files

    # 4. Generate and save the report to a file
    report_path = os.path.join(os.path.dirname(__file__), 'file_completeness_report.txt')
    with open(report_path, 'w', encoding='utf-8') as report_file:
        report_file.write("--- Raport kompletności plików ---\n")
        report_file.write(f"Data sprawdzenia: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if not missing_input_files:
            report_file.write(f"✅ Folder 'input' jest kompletny. Znaleziono wszystkie {len(expected_input_files)} zdefiniowane pliki.\n\n")
        else:
            report_file.write(f"❌ Znaleziono braki w folderze 'input' ({len(missing_input_files)} z {len(expected_input_files)}):\n")
            for file in sorted(list(missing_input_files)):
                report_file.write(f"  - {file}\n")
            report_file.write("\n")

        if not missing_mockup_files:
            report_file.write(f"✅ Folder 'mockup' jest kompletny. Znaleziono wszystkie {len(expected_mockup_files)} zdefiniowane pliki.\n\n")
        else:
            report_file.write(f"❌ Znaleziono braki w folderze 'mockup' ({len(missing_mockup_files)} z {len(expected_mockup_files)}):\n")
            for file in sorted(list(missing_mockup_files)):
                report_file.write(f"  - {file}\n")
            report_file.write("\n")

        report_file.write("--- Koniec raportu ---\n")

    print(f"Raport został zapisany w pliku: {report_path}")

if __name__ == "__main__":
    check_file_completeness()
