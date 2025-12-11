import sys
import os
import struct
import binascii

# Add the directory containing this script to the Python path
# to resolve the ModuleNotFoundError for 'export_to_json'.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from export_to_json import export_to_json



def unpack_dat_file():
    print("""
    =====================================================================
                Binary Data Extractor (Key-Value Pairs)
    =====================================================================
    This script parses a binary file to extract key-value pairs based on a 
    specific format:

      - Skips a fixed 14-byte file header.
      - Reads a 4-byte signed integer for Key length.
        - Positive length indicates a null-terminated UTF-8 string.
        - Negative length indicates a null-terminated UTF-16 string.
      - Reads a 4-byte signed integer for Value length with the same logic.
      - Exports all extracted data to a JSON file.
    """)
    file_path = input("Enter the name of the binary file(.dat) to extract: ")

    if not os.path.exists(file_path):
        print(f"Error: File not found at path {file_path}")
        return

    OUTPUT_FILE_PATH = "extracted_localization_" + os.path.basename(file_path).replace('.', '_') + ".json"

    LENGTH_FIELD_SIZE = 4
    MAX_SAFE_KEY_LENGTH = 20 * 1024
    MAX_SAFE_VALUE_LENGTH = 10 * 1024 * 1024

    HEADER_SIZE = 14

    extracted_data = []  # This is a LIST

    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    i = 0
    data_len = len(data)
    print(f"File size: {data_len} byte ({data_len:X} HEX)")

    if data_len >= HEADER_SIZE:
        i = HEADER_SIZE
        print(f"-> Header omitted ({HEADER_SIZE} bytes). Start parsing from {i:X} HEX.")
    else:
        print("Warning: File is too small.")

    def read_length_field(data_slice, signed=False):
        if len(data_slice) < LENGTH_FIELD_SIZE:
            return None
        raw_length = data_slice[0:LENGTH_FIELD_SIZE]
        if signed:
            return struct.unpack('<i', raw_length)[0]
        else:
            return struct.unpack('<I', raw_length)[0]

    while i < data_len:
        # --- --- --- --- --- --- ---
        # --- KEY READING BLOCK (no changes to logic, omitted for brevity) ---
        # --- --- --- --- --- --- ---
        if i + LENGTH_FIELD_SIZE > data_len: break
        key_length_start = i
        key_length_signed = read_length_field(data[key_length_start: key_length_start + LENGTH_FIELD_SIZE], signed=True)
        key_data_start = key_length_start + LENGTH_FIELD_SIZE

        key_data_type = "UTF-8"
        if key_length_signed >= 0:
            current_key_length_with_terminator = key_length_signed
        else:
            current_key_length_with_terminator = abs(key_length_signed) * 2
            key_data_type = "UTF-16"

        if current_key_length_with_terminator <= 0 or current_key_length_with_terminator > MAX_SAFE_KEY_LENGTH:
            # print(f"Skip key at {key_length_start:X}") # Debug
            i += 1;
            continue

        key_data_end = key_data_start + current_key_length_with_terminator
        if key_data_end > data_len: break

        raw_key_data_with_terminator = data[key_data_start: key_data_end]

        if key_data_type == "UTF-8":
            raw_key_string = raw_key_data_with_terminator[:-1]
            encoding = 'utf-8'
        else:
            raw_key_string = raw_key_data_with_terminator[:-2]
            encoding = 'utf-16-le'

        try:
            current_key = raw_key_string.decode(encoding, errors='replace')
        except:
            current_key = binascii.hexlify(raw_key_string).decode('ascii')

        # --- --- --- --- --- --- ---
        # --- VALUE READING BLOCK ---
        # --- --- --- --- --- --- ---

        value_length_field_start = key_data_end
        if value_length_field_start + LENGTH_FIELD_SIZE > data_len: break

        value_length_signed = read_length_field(
            data[value_length_field_start: value_length_field_start + LENGTH_FIELD_SIZE], signed=True)
        value_data_start = value_length_field_start + LENGTH_FIELD_SIZE

        is_length_error = False
        value_data_type = "UTF-8"  # Default

        if value_length_signed >= 0:
            value_length_bytes = value_length_signed
            value_data_type = "UTF-8"
        else:
            value_length_bytes = abs(value_length_signed) * 2
            value_data_type = "UTF-16"

        value_data_end = value_data_start + value_length_bytes

        # Length validation check

        if value_data_end > data_len or value_length_bytes > MAX_SAFE_VALUE_LENGTH:
            print(f"!!! VALUE LENGTH ERROR !!! Key '{current_key}'. Skip.")
            is_length_error = True

        if is_length_error:
            i = value_data_start  # Attempt at recovery
            continue

        raw_value_data = data[value_data_start: value_data_end]

        if value_data_type == "UTF-8":
            # Safe cut, even if the length is 0
            decoded_value = raw_value_data[:-1].decode('utf-8', errors='replace') if len(raw_value_data) > 0 else ""
        else:
            decoded_value = raw_value_data[:-2].decode('utf-16-le', errors='replace') if len(raw_value_data) > 1 else ""

        extracted_data.append({
            "Key": current_key,
            "Value": decoded_value,
            "Key_Type": key_data_type,
            "Localization_Value": "",
            "Localization_Data_Type": "1",
        })

        i = value_data_end

    # --- ИСПРАВЛЕННЫЙ БЛОК ВЫВОДА ---
    try:
        if extracted_data:
            print("\n✨ Data extraction results (First 5):")
            # [FIX 1] Используем переменную `item`, чтобы не затереть список `extracted_data`
            for idx, item in enumerate(extracted_data[:5]):
                print("=" * 70)
                print(f"🔑 Key: **{item['Key']}** (Type: {item['Key_Type']})")
                # [FIX 2] Используем item['Value_Type'] для отображения
                print(f"  > Value: '{item['Value']}' ")
                if idx == 4:
                    break

        # Теперь `extracted_data` всё ещё список, и экспорт сработает
        export_to_json(extracted_data, OUTPUT_FILE_PATH)
        print(f"\nSuccessfully saved in: {OUTPUT_FILE_PATH}")

    except Exception as e:
        print(f"\n❌ Error writing to file: {e}")
        import traceback
        traceback.print_exc()
