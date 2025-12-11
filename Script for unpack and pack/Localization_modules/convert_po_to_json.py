import json
import os
import polib

def convert_po_to_json_polib():
    po_input_path = input("Введите путь к PO-файлу для конвертации в JSON: ")
    if not os.path.exists(po_input_path):
        print(f"Error: File not found at path {po_input_path}")
        return
    # Имя выходного JSON-файла
    json_output_path = "translations_from_po.json"
    """
    Загружает данные из PO-файла с помощью polib, извлекает msgctxt (Key),
    msgid (Value) и msgstr (Russian_Value), и экспортирует их в JSON-файл.

    :param po_input_path: Путь к входному PO-файлу.
    :param json_output_path: Путь к выходному JSON-файлу.
    """

    print(f"📖 Загрузка PO-файла: {po_input_path}...")

    # 1. Загрузка данных из PO-файла с помощью polib
    try:
        # polib автоматически обрабатывает экранирование и многострочность
        po = polib.pofile(po_input_path)
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл не найден по пути {po_input_path}")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении или парсинге PO-файла: {e}")
        return

    json_data = []

    # 2. Парсинг записей
    for entry in po:
        # Пропускаем заголовок файла (первую запись)
        if entry.msgid == '' or entry.msgctxt is None:
            continue

        # Убираем записи, помеченные как устаревшие (обязательно в polib)
        if entry.obsolete:
            continue

        key = entry.msgctxt.strip() if entry.msgctxt else ""  # msgctxt (Key)

        # Пропускаем, если msgctxt (Key) отсутствует после strip()
        if not key:
            # Обычно в PO-файлах, если нет msgctxt, используется msgid как ключ,
            # но в вашем формате нужен именно msgctxt.
            # Для вашего случая лучше пропустить
            continue

        original_value = entry.msgid  # msgid (Value)
        Localization_value = entry.msgstr  # msgstr (Localization_Value)

        # Добавляем запись в формат JSON
        json_data.append({
            "Key": key,
            # polib гарантирует, что эти значения уже разэкранированы
            # и готовы для прямого использования в JSON
            # "Value": original_value,
            "Key_Type": "UTF-8",
            "Localization_Value": Localization_value,
            "Localization_Data_Type": 1
        })

    # 3. Сохранение JSON-файла
    try:
        with open(json_output_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False важен для сохранения русских символов как есть
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"\n🎉 Успех! Создан JSON-файл: {os.path.basename(json_output_path)}")
        print(f"📊 Импортировано записей: {len(json_data)}")

    except Exception as e:
        print(f"❌ Ошибка при записи JSON-файла: {e}")