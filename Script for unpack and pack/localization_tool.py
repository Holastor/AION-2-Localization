import struct
import json
import os
import binascii
import pandas as pd
import csv
import re
import polib

# --- ОСНОВНЫЕ ФУНКЦИИ ОБРАБОТКИ ДАННЫХ ---

def extract_key_value_filtered_v6_4(file_path):
    """
    Извлекает пары Key-Value из бинарного файла, используя 4-байтовые поля длины.
    Поддерживает UTF-8 и UTF-16 для Key и Value.
    
    ДОБАВЛЕНО: Пропуск фиксированного 14-байтового заголовка файла.
    """
    
    LENGTH_FIELD_SIZE = 4
    MAX_SAFE_KEY_LENGTH = 20 * 1024 
    MAX_SAFE_VALUE_LENGTH = 10 * 1024 * 1024 
    
    # ФИКСИРОВАННЫЙ РАЗМЕР ЗАГОЛОВКА
    HEADER_SIZE = 14 
    
    extracted_data = []
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {file_path}")
        return []
    
    i = 0
    data_len = len(data)
    print(f"Размер файла: {data_len} байт ({data_len:X} HEX)")

    # --- СМЕЩЕНИЕ НАЧАЛА ---
    if data_len >= HEADER_SIZE:
        i = HEADER_SIZE
        print(f"-> Пропущен заголовок ({HEADER_SIZE} байт). Начало парсинга с {i:X} HEX.")
    else:
        print("Предупреждение: Файл слишком мал для заголовка. Начинаем с 0.")
    # ----------------------

    def read_length_field(data_slice, signed=False):
        if len(data_slice) < LENGTH_FIELD_SIZE:
            return None
        raw_length = data_slice[0:LENGTH_FIELD_SIZE]
        if signed:
            return struct.unpack('<i', raw_length)[0]
        else:
            return struct.unpack('<I', raw_length)[0]

    while i < data_len:
        
        # 1. Чтение 4-байтового поля длины Key
        if i + LENGTH_FIELD_SIZE > data_len:
            break

        key_length_start = i
        
        key_length_signed = read_length_field(data[key_length_start : key_length_start + LENGTH_FIELD_SIZE], signed=True)
        
        key_data_start = key_length_start + LENGTH_FIELD_SIZE
        
        # --- ФИЛЬТР И ОПРЕДЕЛЕНИЕ КОДИРОВКИ KEY ---
        key_data_type = "UTF-8" # По умолчанию
        
        if key_length_signed >= 0:
            current_key_length_with_terminator = key_length_signed
        else: # Отрицательное значение для Key Length означает UTF-16
            current_key_length_with_terminator = abs(key_length_signed) * 2 
            key_data_type = "UTF-16"
        
        if current_key_length_with_terminator <= 0 or current_key_length_with_terminator > MAX_SAFE_KEY_LENGTH:
            print(f"Предупреждение: Некорректная/нереалистичная длина Key ({key_length_signed}) на {key_length_start:X}. Пропуск 1 байта.")
            i += 1 
            continue
        
        key_data_end = key_data_start + current_key_length_with_terminator
        
        if key_data_end > data_len:
            print(f"Ошибка: Key Length ({key_length_signed}) выходит за пределы файла. Остановка.")
            break
            
        raw_key_data_with_terminator = data[key_data_start : key_data_end]
        
        # 2. Извлечение Key String (KeyData)
        if key_data_type == "UTF-8":
            raw_key_string = raw_key_data_with_terminator[:-1]
            key_terminator_len = 1
            encoding = 'utf-8'
        else: # UTF-16
            raw_key_string = raw_key_data_with_terminator[:-2]
            key_terminator_len = 2
            encoding = 'utf-16-le'
        
        # Проверка терминатора
        if len(raw_key_data_with_terminator) < key_terminator_len or raw_key_data_with_terminator[-key_terminator_len:] != (b'\x00' * key_terminator_len):
             print(f"Предупреждение: Key на {key_length_start:X} не заканчивается корректным терминатором ({key_data_type}).")

        try:
            current_key = raw_key_string.decode(encoding, errors='replace')
        except:
            current_key = binascii.hexlify(raw_key_string).decode('ascii')
            
        # 3. Чтение 4-байтового поля длины Value (со знаком)
        value_length_field_start = key_data_end
        
        if value_length_field_start + LENGTH_FIELD_SIZE > data_len:
            print(f"Ошибка: Key '{current_key}' найден, но нет 4-байтового поля длины Value на {value_length_field_start:X}. Остановка.")
            break

        value_length_signed = read_length_field(data[value_length_field_start : value_length_field_start + LENGTH_FIELD_SIZE], signed=True)
        
        value_data_start = value_length_field_start + LENGTH_FIELD_SIZE
        
        # 4. Диспетчер длины и кодировки Value
        is_length_error = False
        
        if value_length_signed >= 0:
            value_length_bytes = value_length_signed
            value_data_end = value_data_start + value_length_bytes
            value_data_type = "UTF-8"
            
            if value_data_end > data_len or value_length_bytes > MAX_SAFE_VALUE_LENGTH:
                print(f"!!! ОШИБКА ДЛИНЫ !!! Key '{current_key}'. Объявленная длина Value ({value_length_bytes}) нереалистична/выходит за пределы файла. Пропуск блока.")
                is_length_error = True
            
        else:
            value_length_bytes = abs(value_length_signed) * 2 
            value_data_end = value_data_start + value_length_bytes
            value_data_type = "UTF-16"
            
            if value_data_end > data_len or value_length_bytes > MAX_SAFE_VALUE_LENGTH:
                print(f"!!! ОШИБКА ДЛИНЫ !!! Key '{current_key}'. Объявленная длина Value ({value_length_bytes} байт) нереалистична/выходит за пределы файла. Пропуск блока.")
                is_length_error = True
        
        # --- ЛОГИКА ПРОПУСКА ПРИ ОШИБКЕ ДЛИНЫ ---
        if is_length_error:
            i = value_data_start
            print(f"--> Начат поиск следующего Key Length от позиции: {i:X}")
            continue
        # --- КОНЕЦ ЛОГИКИ ПРОПУСКА ---
        
        # 5. Извлечение Value (Если ошибки нет)
        raw_value_data = data[value_data_start : value_data_end]

        if value_data_type == "UTF-8":
            decoded_value = raw_value_data[:-1].decode('utf-8', errors='replace')
        else:
            decoded_value = raw_value_data[:-2].decode('utf-16-le', errors='replace')
        
        # Собираем данные для JSON
        extracted_data.append({
            "Key": current_key,
            "Value": decoded_value,
            "Key_Type": key_data_type,
            "Russian_Value": "", # Оставляем пустым для перевода
            "Russian_Data_Type": "", 
        })
        
        i = value_data_end
            
    return extracted_data

def export_to_json(data, filename="output_data.json"):
    """Экспортирует список словарей в JSON-файл."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4) 
        print(f"\n✅ Данные успешно экспортированы в файл: {filename}")
        print(f"   Объектов экспортировано: {len(data)}")
    except Exception as e:
        print(f"\n❌ Ошибка при экспорте в JSON: {e}")

def create_binary_from_json_v7_6(json_file_path, output_file_path="repacked_l10n.dat"):
    """
    Преобразует данные из JSON-файла обратно в бинарный файл.
    Добавляет специфический заголовок, использует оптимизацию b''.join().
    """
    
    # Специфический заголовок файла (14 байт)
    HEADER_BYTES = b'\x06\x00\x00\x00' + b'AION2\x00' + b'\x70\xEA\x01\x00'
    
    packed_parts = []
    data_to_pack = []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data_to_pack = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: JSON-файл не найден по пути {json_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Ошибка: Некорректный JSON-файл. {e}")
        return

    # --- ДОБАВЛЕНИЕ ЗАГОЛОВКА В САМОЕ НАЧАЛО ---
    packed_parts.append(HEADER_BYTES)
    
    total_items = len(data_to_pack)
    print(f"Начато создание бинарного файла из {total_items} записей...")
    print(f"-> Добавлен заголовок файла ({len(HEADER_BYTES)} байт).")

    for index, item in enumerate(data_to_pack):
        
        key_str = item.get('Key', '')
        
        # Получаем Russian_value и проверяем его на пустоту
        raw_value_str = str(item.get('Russian_Value', ''))
        value_str_stripped = raw_value_str.strip()
        
        # --- 1. ФИЛЬТРАЦИЯ ПУСТЫХ ПЕРЕВОДОВ ---
        if not value_str_stripped:
            print(f"[{index + 1}/{total_items}] ПРОПУСК: Key '{key_str[:60]}' имеет пустое Russian_Value.")
            continue
        
        value_str_to_pack = raw_value_str
        # ----------------------------------------------------
        
        # Чтение типов из JSON-выгрузки
        key_data_type = item.get('Key_Type', 'UTF-8').upper() 
        # value_data_type_structural = item.get('Value_Type', 'UTF-8').upper() 
        
        # --- 2. ОПРЕДЕЛЕНИЕ ТИПА ПО ФЛАГУ (0/1) ---
        russian_data_type_flag = item.get('Russian_Data_Type')
        # value_data_type = value_data_type_structural

        if russian_data_type_flag is not None:
            try:
                flag = int(russian_data_type_flag)
                if flag == 1:
                    value_data_type = 'UTF-16'
                elif flag == 0:
                    value_data_type = 'UTF-8'
            except (ValueError, TypeError):
                pass
        # -------------------------------------------------------
        
        # --- ОТСЛЕЖИВАНИЕ ПРОГРЕССА ---
        print(f"[{index + 1}/{total_items}] Пакую Key: {key_str[:60]}... (Value Type: {value_data_type})")
        # -----------------------------

        # --- 3. Key Data и Key Length ---
        
        if key_data_type == 'UTF-8':
            key_data_with_terminator = key_str.encode('utf-8') + b'\x00'
            key_length_signed = len(key_data_with_terminator)
            
        elif key_data_type == 'UTF-16':
            encoded_data = key_str.encode('utf-16-le')
            key_data_with_terminator = encoded_data + b'\x00\x00'
            
            key_byte_length = len(key_data_with_terminator)
            symbol_count = key_byte_length // 2
            key_length_signed = -symbol_count
            
        else:
            print(f"Предупреждение: Неизвестный тип Key '{key_data_type}' для Key '{key_str}'. Пропуск.")
            continue

        # Запись Key Length (4 байта, <i)
        packed_parts.append(struct.pack('<i', key_length_signed)) 
        # Запись Key Data
        packed_parts.append(key_data_with_terminator) 

        # --- 4. Value Data и Value Length (Используем Russian_value) ---
        
        if value_data_type == 'UTF-8':
            value_data_with_terminator = value_str_to_pack.encode('utf-8') + b'\x00'
            value_length_signed = len(value_data_with_terminator)
            
        elif value_data_type == 'UTF-16':
            encoded_data = value_str_to_pack.encode('utf-16-le')
            value_data_with_terminator = encoded_data + b'\x00\x00'
            
            value_byte_length = len(value_data_with_terminator)
            symbol_count = value_byte_length // 2
            value_length_signed = -symbol_count
            
        else:
            print(f"Предупреждение: Неизвестный тип Value '{value_data_type}' для Key '{key_str}'. Пропуск.")
            continue
            
        # Запись Value Length (4 байта, <i, так как может быть отрицательным)
        packed_parts.append(struct.pack('<i', value_length_signed)) 
        # Запись Value Data
        packed_parts.append(value_data_with_terminator) 

    # --- 5. Запись в файл ---
    try:
        final_packed_bytes = b''.join(packed_parts)
        
        with open(output_file_path, 'wb') as f:
            f.write(final_packed_bytes)
            
        print(f"\n✅ Успешно записано в бинарный файл: {output_file_path}")
        print(f"   Общий размер файла: {len(final_packed_bytes)} байт ({len(final_packed_bytes):X} HEX)")
    except Exception as e:
        print(f"\n❌ Ошибка при записи в файл: {e}")

# def unescape_po_string(text):
#     """
#     Убирает экранирование, специфичное для PO-файлов (обратный слэш, двойные кавычки, \n),
#     в правильном порядке.
#     """
#     text = str(text)
    
#     # 1. Заменяем двойной слэш на временную метку, чтобы не сломать \n и \"
#     text = text.replace('\\\\', '\u0001') # \u0001 — это просто временный уникальный маркер
    
#     # 2. Убираем экранирование \n и \"
#     text = text.replace('\\n', '\n')
#     text = text.replace('\\"', '"')
    
#     # 3. Восстанавливаем слэши
#     text = text.replace('\u0001', '')
    
#     # **Дополнительный важный шаг для PO:** # Обработка конкатенации строк (если ваш regex ее не ловит)
#     text = text.sub(r'"\s*"', '', text) 
    
#     return text

def convert_po_to_json_polib(po_input_path, json_output_path):
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

        key = entry.msgctxt.strip() if entry.msgctxt else "" # msgctxt (Key)
        
        # Пропускаем, если msgctxt (Key) отсутствует после strip()
        if not key:
             # Обычно в PO-файлах, если нет msgctxt, используется msgid как ключ, 
             # но в вашем формате нужен именно msgctxt.
             # Для вашего случая лучше пропустить
             continue
             
        original_value = entry.msgid          # msgid (Value)
        russian_value = entry.msgstr        # msgstr (Russian_Value)

        # Добавляем запись в формат JSON
        json_data.append({
            "Key": key,
            # polib гарантирует, что эти значения уже разэкранированы 
            # и готовы для прямого использования в JSON
            "Value": original_value,
            "Key_Type": "UTF-8",      
            "Russian_Value": russian_value,
            "Russian_Data_Type": 1     
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

# Убираем агрессивную нормализацию (normalize_key и clean_key_for_writing)

def format_po_string(text):
    return str(text).strip()

def get_po_file(po_path):
    """Загружает или создает PO-файл с помощью polib."""
    try:
        po = polib.pofile(po_path)
    except FileNotFoundError:
        # Если файл не найден, создаем новый
        po = polib.POFile()
    except Exception as e:
        print(f"❌ Критическая ошибка при загрузке PO-файла: {e}. Создается пустой POFile.")
        po = polib.POFile()
    return po

def update_po_from_json(json_input_path, po_target_path):
    """
    Загружает JSON, сравнивает его с существующим PO-файлом, и перезаписывает файл, 
    удаляя старые записи, если Value отличается.
    
    ДОБАВЛЕНО: Сохранение старого перевода (msgstr) в виде комментария.
    """
    
    # 1. Загрузка данных из JSON
    try:
        with open(json_input_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при загрузке JSON: {e}")
        return
    
    # 2. Загрузка PO-файла и создание словаря-источника (Key -> POEntry)
    po = get_po_file(po_target_path)
    
    # Индексируем существующие записи в PO для быстрого доступа
    # {msgctxt: POEntry}
    po_entry_map = {entry.msgctxt.strip(): entry for entry in po if entry.msgctxt}

    # 3. Создание нового, чистого списка записей
    
    new_po = polib.POFile()
    keys_processed = set()
    
    records_to_insert = 0
    records_to_update = 0
    records_to_skip = 0
    
    # 4. Проход по JSON (источнику истины)
    
    for item in json_data:
        key = item.get('Key', '')
        original_value = item.get('Value', '')
        russian_value = item.get('Russian_value', '') 
        
        if not key or not original_value:
            continue
            
        key_for_comparison = format_po_string(key)
        value_from_json = format_po_string(original_value)
        
        if key_for_comparison in po_entry_map:
            # Key существует в старом PO-файле
            existing_entry = po_entry_map.pop(key_for_comparison) # Удаляем из карты
            value_from_po = existing_entry.msgid.strip()
            
            if value_from_json != value_from_po:
                # 4a. Value отличается: UPDATE
                
                # --- ЛОГИКА СОХРАНЕНИЯ СТАРОГО ПЕРЕВОДА ---
                old_msgstr = existing_entry.msgstr.strip()
                old_comment = existing_entry.comment
                
                # Добавляем старый перевод в комментарий, если он не пуст
                if old_msgstr:
                    old_comment = f"(OLD TRANSLATION: {old_msgstr})"
                    if existing_entry.comment:
                        old_comment = existing_entry.comment + "\n" + old_comment
                
                # Создаем новую запись, используя данные из JSON (новый Value)
                new_entry = polib.POEntry(
                    msgctxt=item.get('Key', ''),
                    msgid=item.get('Value', ''),
                    msgstr=item.get('Russian_value', ''), # Оставляем перевод из JSON (или пустой)
                    comment=old_comment,
                    # tcomment=f"Original Value Type: {item.get('Value_Type', 'N/A')}",
                    flags=['fuzzy'] # Отмечаем как fuzzy, так как msgid изменился
                )
                new_po.append(new_entry)
                records_to_update += 1
                
            else:
                # 4b. Key и Value совпадают: SKIP (сохраняем старую запись PO)
                # Копируем старую запись (сохраняя существующий перевод)
                new_po.append(existing_entry)
                records_to_skip += 1
                
        else:
            # 4c. Key не существует: INSERT
            new_entry = polib.POEntry(
                msgctxt=item.get('Key', ''),
                msgid=item.get('Value', ''),
                msgstr=item.get('Russian_value', ''),
            )
            new_po.append(new_entry)
            records_to_insert += 1

    # 5. Сохранение обновленного PO-файла (Перезапись)
    
    try:
        new_po.save(po_target_path)
        
        print("\n--- Результат Полной Пересборки PO ---")
        print(f"🎉 Файл {os.path.basename(po_target_path)} успешно обновлен (перезаписан).")
        print(f"🔄 Обновлено записей (Value отличался): {records_to_update}")
        print(f"➕ Добавлено новых записей (INSERT): {records_to_insert}")
        print(f"🗑️ Удалено старых/лишних записей: {len(po_entry_map)}")
        print(f"⏭️ Пропущено (Key и Value совпали): {records_to_skip}")
        
    except Exception as e:
        print(f"❌ Ошибка при записи PO-файла: {e}")

        
# --- РЕЖИМЫ РАБОТЫ ---

def jsontohex():
    # Ввод файла от пользователя
    INPUT_JSON_PATH = input("Введите путь или имя JSON файла для упаковки: ")
    OUTPUT_BIN_PATH = "repacked_L10NString_RU.dat" 
    
    # 1. Запуск упаковщика
    create_binary_from_json_v7_6(INPUT_JSON_PATH, OUTPUT_BIN_PATH)

def hextojson():
    # ⚠️ ЗАМЕНИТЕ ЭТОТ ПУТЬ НА ПУТЬ К ВАШЕМУ ФАЙЛУ
    YOUR_FILE_PATH = input("Введите имя бинарного файла для извлечения: ")
    OUTPUT_FILE_PATH = "extracted_localization_" + os.path.basename(YOUR_FILE_PATH).replace('.', '_') + ".json"
    
    results = extract_key_value_filtered_v6_4(YOUR_FILE_PATH) 

    if results:
        print("\n✨ Результаты извлечения данных (Первые 5):")
        for idx, result in enumerate(results[:5]):
            print("=" * 70)
            print(f"🔑 Key: **{result['Key']}** (Type: {result['Key_Type']})")
            print(f"  > Value: '{result['Value']}' (Type: {result['Russian_Data_Type']})")
            if idx == 4:
                break
        export_to_json(results, OUTPUT_FILE_PATH)
    else:
        print("Данные Key-Value не найдены или произошла критическая ошибка.")
def potojson():
    INPUT_PO_FILE = input("Введите путь к PO-файлу для конвертации в JSON: ")
    
    # Имя выходного JSON-файла
    OUTPUT_JSON_FILE = "translations_from_po.json"
    
    convert_po_to_json_polib(INPUT_PO_FILE, OUTPUT_JSON_FILE)

def poupdate():
    INPUT_JSON_PATH = input("Введите путь к JSON-файлу с новыми данными: ")
    
    # Целевой PO-файл (который будет обновлен)
    OUTPUT_PO_PATH = "localization_template.po"
    
    update_po_from_json(INPUT_JSON_PATH, OUTPUT_PO_PATH)
# def jsontocsv():
#     # Имя исходного JSON файла
#     INPUT_JSON_FILE = input("Введите имя JSON файла для конвертации в CSV: ")
    
#     # Имя выходного CSV файла
#     OUTPUT_CSV_FILE = "extracted_localization_" + os.path.basename(INPUT_JSON_FILE).replace('.', '_') + ".csv"
    
#     # Список столбцов для извлечения 
#     COLUMNS_TO_EXTRACT = ['Key', 'Original_Value', 'Russian_Value'] 
    
#     extract_keys_values_to_csv(INPUT_JSON_FILE, OUTPUT_CSV_FILE, COLUMNS_TO_EXTRACT)

# def csvtojson():
#     INPUT_JSON_PATH = input("INPUT_JSON_PATH ")
    
#     # 2. CSV-файл, содержащий переводы (output.csv или результат фильтрации)
#     INPUT_CSV_PATH = input("INPUT_CSV_PATH")
    
#     # 3. Куда сохранить JSON с переводами
#     OUTPUT_JSON_PATH = "final_localization_RU.json" 
    
#     # 4. Имя столбца в CSV, который соответствует 'Key' в JSON
#     KEY_COLUMN_CSV = 'Key' # <--- СКОРЕЕ ВСЕГО, 'id' ИСПОЛЬЗУЕТСЯ ДЛЯ СОПОСТАВЛЕНИЯ
    
#     # 5. Имя столбца в CSV, который содержит готовый русский перевод
#     TRANSLATION_COLUMN_CSV = 'Russian_Value' # <--- ЗАМЕНИТЕ НА РЕАЛЬНОЕ ИМЯ СТОЛБЦА С ПЕРЕВОДОМ
    
    
#     # Запуск функции
#     inject_translations_from_csv(
#         INPUT_JSON_PATH, 
#         INPUT_CSV_PATH, 
#         OUTPUT_JSON_PATH,
#         key_column_in_csv=KEY_COLUMN_CSV,
#         translation_column_in_csv=TRANSLATION_COLUMN_CSV
#     )

# def mergejson():
#     BASE_FILE = input("Введите путь к ОСНОВНОМУ JSON (File A): ")
    
#     # 2. Исходный файл (File B - источник обновлений и новых данных)
#     SOURCE_FILE = input("Введите путь к ИСХОДНОМУ JSON (File B): ")
    
#     # 3. Выходной файл (объединенный результат)
#     OUTPUT_FILE = "merged_delete_append_localization.json"
    
#     # 4. Поле для сравнения ключей
#     KEY_FIELD_NAME = 'Key'
    
#     # 5. Поле для сравнения значений
#     VALUE_FIELD_NAME = 'Value' 
    
#     # Запуск функции
#     merge_json_files_delete_append(
#         base_json_path=BASE_FILE,
#         source_json_path=SOURCE_FILE,
#         output_json_path=OUTPUT_FILE,
#         key_field=KEY_FIELD_NAME,
#         value_field=VALUE_FIELD_NAME
#     )
# # --- ГЛАВНЫЙ ИСПОЛНЯЕМЫЙ БЛОК ---

if __name__ == '__main__':
    print("--- ИНСТРУМЕНТ ЛОКАЛИЗАЦИИ AION2 ---")
    mode = input("Выберите режим (1-HexToJson, 2-JsonToHex, 3-PoToJson, 4-PoUpdate, 5-MergeJson): ")
    
    if mode == "1":
        hextojson()
    elif mode =="2":
        jsontohex()
    elif mode =="3":
        potojson()
    elif mode =="4":
        poupdate()
    # elif mode =="5":
    #     mergejson()        
    else:
        print("Неверный режим. Пожалуйста, введите 1, 2, 3, 4 или 5.")