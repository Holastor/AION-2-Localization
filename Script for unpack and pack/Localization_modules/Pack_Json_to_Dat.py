import struct
import json
import os

def pack_json_to_dat():
    print("""
    =====================================================================
                JSON to Binary (.dat) Repacker
    =====================================================================
    This tool converts localization data from JSON back to binary format.
      - Input: Your translated JSON file.
      - Source Field: Uses 'Localization_Value' for text.
      - Filtering: SKIPS records with empty translations.
      - Output: Generates 'repacked_L10NString.dat' with correct header/encoding.
    """)

    json_file_path = input("Enter the path or name of the JSON file to package: ")
    if not os.path.exists(json_file_path):
        print(f"Error: File not found at path {json_file_path}")
        return

    output_file_path = "repacked_L10NString.dat"

    """
    Converts data from a JSON file back into a binary file.
    Adds a specific header, uses b''.join() optimization.
    """

    # Specific file header (14 bytes) MUST ALWAYS BE LIKE THIS!!!
    HEADER_BYTES = b'\x06\x00\x00\x00' + b'AION2\x00' + b'\x70\xEA\x01\x00'

    packed_parts = []
    data_to_pack = []

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data_to_pack = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at path {json_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file. {e}")
        return

    # --- ADD HEADER AT THE VERY BEGINNING OF THE FILE ---

    packed_parts.append(HEADER_BYTES)

    total_items = len(data_to_pack)
    print(f"Starting to create a binary file from {total_items} records...")
    print(f"-> File header added ({len(HEADER_BYTES)} bytes).")

    for index, item in enumerate(data_to_pack):

        key_str = item.get('Key', '')

        # Get Localization_value and check if it is empty
        raw_value_str = str(item.get('Localization_Value', ''))
        value_str_stripped = raw_value_str.strip()

        # --- 1. FILTERING EMPTY TRANSLATIONS ---
        if not value_str_stripped:
            print(f"[{index + 1}/{total_items}] PASS: Key ‘{key_str[:60]}’ has an empty Localization_Value.")
            continue

        value_str_to_pack = raw_value_str
        # ----------------------------------------------------

        # Reading types from JSON dump
        key_data_type = item.get('Key_Type', 'UTF-8').upper()
        # value_data_type_structural = item.get('Value_Type', 'UTF-8').upper()

        # --- 2. DETERMINING THE TYPE BY FLAG (0/1) - IS THIS NECESSARY?--
        russian_data_type_flag = item.get('Localization_Data_Type')
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

        # --- TRACKING PROGRESS ---
        print(f"[{index + 1}/{total_items}] Pack Key: {key_str[:60]}... (Value Type: {value_data_type})")
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
            print(f"Warning: Unknown type Key ‘{key_data_type}’ for Key ‘{key_str}’. Omitted.")
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
            print(f"Warning: Unknown type Value ‘{value_data_type}’ for Key ‘{key_str}’. Omitted.")
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

        print(f"\n✅ Successfully saved to binary file: {output_file_path}")
        print(f"   Total file size: {len(final_packed_bytes)} byte ({len(final_packed_bytes):X} HEX)")
    except Exception as e:
        print(f"\n❌ Error writing to file: {e}")