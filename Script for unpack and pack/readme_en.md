# 📘 AION2 Localization Tool User Guide

This set of scripts is designed to unpack, translate, update, and repack game language files (`.dat` format) using `.json` and `.po` (Gettext) as intermediate formats.

## 🛠 Installation and Setup

### 1. Requirements
To use this tool, **Python 3** must be installed on your computer.

*   **macOS:** Usually pre-installed. If not, enter the following in the terminal:
    ```bash
    brew install python
    ```
    or download it from [python.org](https://www.python.org/).
*   **Windows:** Download and install from [python.org](https://www.python.org/).
    > [!IMPORTANT]
    > Make sure to check the box **"Add Python to PATH"** during installation.

### 2. First Run
The script folder contains a launch file:
*   🍎 **macOS:** `run_tool.command`
*   🪟 **Windows:** `run_tool.bat`

**When launching via `run_tool.command` or `run_tool.bat`:** The script will automatically check for Python and the required `polib` library. If the library is missing, it will prompt you to install it (Press `Y` and `Enter`).

---

## 🚀 Main Workflows

The tool operates via a main menu with 6 modes. Each mode is described below.

### 1️⃣ Unpacking Game Files (DAT → JSON)
Used to extract text from the original game binary file.

1.  Select option **1**.
2.  Enter the path to the `.dat` file (e.g., `L10NString.dat`).
3.  The script will create a file named `extracted_localization_....json`.
    *   This file contains all keys and original texts.

### 2️⃣ Preparing for Translation (JSON → PO Files)
Used to split a massive JSON file into convenient categories (Skills, Quests, UI, etc.) in `.po` format, which is supported by professional editors (such as Poedit).

1.  Select option **3**.
2.  Enter the name of the JSON file obtained in Step 1.
3.  The script will analyze the keys and sort them into folders.
    *   The result will be saved in the folder: `po_dictonaries/`.
    *   Inside, you will find files like `SkillString_ASSASSIN.po`, `QuestString.po`, etc.

> [!TIP]
> **Tip:** Open `.po` files using **Poedit**. It makes translation easy: the original text is on the left, and your translation goes on the right.

### 3️⃣ Building the Translation (PO Files → JSON → DAT)
When you have finished translating in the `.po` files, they need to be assembled back into the game format.

#### Stage A: Merging PO Files
1.  Select option **4**.
2.  Select the source folder (usually `1 - po_dictonaries`).
3.  The script will merge all `.po` files from that folder into one master file: `combine_localization.po`.

#### Stage B: Converting to JSON
1.  Select option **5**.
2.  Enter the filename: `combine_localization.po`.
3.  The script will create a file named `translations_from_po.json`.

#### Stage C: Packing into DAT
1.  Select option **2**.
2.  Enter the filename: `translations_from_po.json`.
3.  The script will create the final game file: `repacked_L10NString.dat`.

> [!WARNING]
> **Important:** The script skips strings with empty translations. Only translated strings will be added to the game.

### 🔄 Sync Localization (Updating Translations)
Used when a new version of the official English translation is released, and you need to migrate your old translation to the new version while marking changes.

1.  Unpack the new `.dat` file from the new game version (see Mode 1) to get a fresh JSON.
2.  Ensure your old translated `.po` files are located in the `po_dictonaries` folder.
3.  Select option **6** in the menu.
4.  Enter the path to the new JSON file.
5.  The script will compare the new file with the old translations:
    *   **New strings:** Added with an empty translation.
    *   **Changed strings:** If the developers changed the English text, the old translation is reset but saved in the "Comments" (marked as "Fuzzy" in Poedit).
    *   **Unchanged strings:** The translation is preserved.
6.  The result is saved in a new folder: `po_comparison/`.
7.  Now work with the files in `po_comparison` as your actual files.

---

## 📋 Menu Quick Reference

| # | Menu Name | Actual Action | Input File | Output File |
|:-:|---|---|---|---|
| **1** | DAT file → JSON file | Unpacks binary file | `.dat` | `.json` |
| **2** | JSON file → DAT file | Packs translation into game format | `.json` | `.dat` |
| **3** | JSON file → PO files | Categorizes and creates dictionaries | `.json` | Folder `po_dictonaries/*.po` |
| **4** | Combine PO files → PO file | Merges all POs into one | Folder with `.po` | `combine_localization.po` |
| **5** | PO file → JSON file | Prepares for packing | `.po` | `.json` |
| **6** | Sync localization | Migrates translation to new version | `.json` (new) + old `.po` | Folder `po_comparison/*.po` |

---

## ⚠️ Troubleshooting

### 1. `ModuleNotFoundError: No module named 'polib'`
*   Run `run_tool.command` or `run_tool.bat`; it will offer to install the module.
*   Or enter the following in your terminal/command prompt:
    ```bash
    pip3 install polib
    ```

### 2. `File not found`
Ensure the file you are trying to access is in the same folder as the `localization_tool.py` script, or provide the full path to the file.

### 3. Encodings
The scripts work with **UTF-8** and **UTF-16 LE**. If you edit JSON files manually, use an editor like **Notepad++** or **VS Code** and save as UTF-8.

### 4. Empty strings in-game
Packing mode (**2**) skips strings where `Localization_Value` is empty. Make sure you have filled in the translations.
