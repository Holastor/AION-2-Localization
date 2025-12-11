import os
import polib
import glob

def combine_po_files():
    print("""
    ===================================================================
                      PO Merger: Combine & Deduplicate
    ===================================================================
    This script consolidates multiple .po files into a single master file:

    1. Prompts for the source directory (Dictionaries or Updates).
    2. Scans for all .po files within the selected folder.
    3. Merges entries into one file, automatically skipping duplicates
       (optimized for speed using Set-based context checking).
    4. Saves the result as 'combine_localization.po'.
    ===================================================================
    """)

    while True:
        dictmode = input(
            "Какую папку использовать?\n введите цифру описывающею директорию словарей: \n 1 - po_dictonaries\n2 - po_update\n0 - exit\nвведите цифру: ")
        match dictmode:
            case "0":
                break
            case "1":
                input_directory = "po_dictonaries"
            case "2":
                input_directory = "po_update"
            case _:
                print("\nIncorrect mode. Please enter 1 or 2\n")
                continue
        break

    output_file_path = "combine_localization.po"
    """
    Находит и объединяет все .po файлы в заданной директории в один мастер-файл.
    УВЕЛИЧЕНИЕ СКОРОСТИ: Использован Set для проверки дубликатов.
    """

    master_po = polib.POFile()

    # 1. Поиск файлов
    search_pattern = os.path.join(input_directory, '**', '*.po')
    all_files = glob.glob(search_pattern, recursive=True)

    if not all_files:
        print("Ошибка", f"Файлы .po не найдены в директории: {input_directory}")
        return

    print(f"✅ Найдено {len(all_files)} файлов для объединения.")
    added_entries_count = 0

    # --- ОПТИМИЗАЦИЯ СКОРОСТИ: Набор существующих контекстов ---
    # Храним все msgctxt в наборе для проверки дубликатов за O(1)
    existing_contexts = set()
    # ------------------------------------------------------------

    # 2. Загрузка и объединение записей
    for file_path in all_files:
        try:
            po_part = polib.pofile(file_path)

            # Если это первый файл, копируем его метаданные в мастер-файл
            if not master_po.metadata:
                master_po.metadata = po_part.metadata

            # Добавляем записи
            for entry in po_part:
                # Пропускаем записи-заголовки
                if entry.msgid == '':
                    continue

                context = entry.msgctxt.strip() if entry.msgctxt else ''

                # ИСПРАВЛЕНИЕ: Проверка дубликатов с использованием Set
                if context not in existing_contexts:
                    master_po.append(entry)
                    existing_contexts.add(context)  # Добавляем новый ключ в набор
                    added_entries_count += 1

            print(f"   + Добавлено записей из: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"❌ Ошибка при обработке файла {os.path.basename(file_path)}: {e}")
            print("Ошибка файла", f"Проблема с файлом {os.path.basename(file_path)}. Пропущен.")
            continue

    # 3. Сохранение финального мастер-файла
    if added_entries_count > 0:
        try:
            master_po.save(output_file_path)
            print(
                "Успех",
                f"Объединение завершено!\nВсего записей добавлено: {added_entries_count}"
            )
            print("\n--- Результат ---")
            print(f"🎉 Объединение успешно завершено. Файл сохранен как: {output_file_path}")
            print(f"📊 Всего записей в мастер-файле: {added_entries_count}")
        except Exception as e:
            print("Ошибка сохранения", f"Не удалось сохранить мастер-файл: {e}")
    else:
        print("Предупреждение", "Не найдено ни одной записи для сохранения.")