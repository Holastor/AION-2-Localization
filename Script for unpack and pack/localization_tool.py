from Localization_modules.Unpack_Dat_File import unpack_dat_file
from Localization_modules.Pack_Json_to_Dat import pack_json_to_dat
from Localization_modules.create_dictionaries_po import categorize_and_export_po
from Localization_modules.combine_po_files import combine_po_files
from Localization_modules.convert_po_to_json import convert_po_to_json_polib
from Localization_modules.sync_new_localization import process_sync


def print_menu():
    print("\n--- --- --- --- --- --- --- ---")
    print("\n--- AION2 LOCALIZATION TOOL ---")
    print("\n--- --- --- --- --- --- --- ---")
    print("\n")
    print("1 - DAT file → JSON file")
    print("2 - JSON file → DAT file")
    print("3 - JSON file → PO files (classified)")
    print("4 - Combine PO files → PO file")
    print("5 - PO file → JSON file")
    print("6 - Sync localization with new update")
    print("0 - Exit\n")


def main():
    actions = {
        "1": unpack_dat_file,
        "2": pack_json_to_dat,
        "3": categorize_and_export_po,
        "4": combine_po_files,
        "5": convert_po_to_json_polib,
        "6": process_sync,
    }

    while True:
        print_menu()
        mode = input("Type number: ").strip()

        if mode == "0":
            print("Exiting...")
            break

        action = actions.get(mode)
        if action:
            try:
                action()
            except Exception as e:
                print(f"❌ Error while executing mode {mode}: {e}")
        else:
            print("⚠️ Incorrect mode. Please enter a valid number.")


if __name__ == "__main__":
    main()

# # # --- ГЛАВНЫЙ ИСПОЛНЯЕМЫЙ БЛОК ---
#
# if __name__ == '__main__':
#     print("--- AION2 LOCALIZATION TOOL ---")
#     while True:
#         mode = input("Select mode: \n1 - DAT file export to JSON file \n2 - JSON file to DAT file \n3 - JSON file is classified and exported to PO files. \n4 - PO files to JSON file \n5 - Po file to Json file \n6 - SYNC localization with new update\n0 - Exit\nType number: \n")
#         match mode:
#             case "0":
#                 break
#             case "1":
#                 unpack_dat_file()
#             case "2":
#                 pack_json_to_dat()
#             case "3":
#                 categorize_and_export_po()
#             case "4":
#                 combine_po_files()
#             case "5":
#                 convert_po_to_json_polib()
#             case "6":
#                 process_sync()
#             case _:
#                   print("\nIncorrect mode. Please enter 1, 2, 3, 4, 5, 6.\n")
#