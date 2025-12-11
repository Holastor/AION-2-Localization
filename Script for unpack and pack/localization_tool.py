from Localization_modules.Unpack_Dat_File import unpack_dat_file
from Localization_modules.Pack_Json_to_Dat import pack_json_to_dat
from Localization_modules.create_dictionaries_po import categorize_and_export_po
from Localization_modules.combine_po_files import combine_po_files
from Localization_modules.convert_po_to_json import convert_po_to_json_polib

# def poupdate():
#     INPUT_JSON_PATH = input("Введите путь к JSON-файлу с новыми данными: ")
#
#     # Целевой PO-файл (который будет обновлен)
#     OUTPUT_PO_PATH = "localization_template.po"
#
#     update_po_from_json(INPUT_JSON_PATH, OUTPUT_PO_PATH)



# # --- ГЛАВНЫЙ ИСПОЛНЯЕМЫЙ БЛОК ---

if __name__ == '__main__':
    print("--- AION2 LOCALIZATION TOOL ---")
    mode = input("Select mode: \n1 - HexToJson \n2 - JsonToHex \n3 - Json To Po's \n4 - PO Files to json \n5 - Po to Json\nType number: ")
    
    if mode == "1":
        unpack_dat_file()
    elif mode =="2":
        pack_json_to_dat()
    elif mode =="3":
        categorize_and_export_po()
    elif mode =="4":
        combine_po_files()
    elif mode =="5":
        convert_po_to_json_polib()
    else:
        print("Incorrect mode. Please enter 1, 2, 3, 4, or 5.")