import os
import json
import re
import polib


def categorize_and_export_po():
    separator = '_'
    input_json_path = input("Введите путь или имя JSON файла для упаковки: ")
    if not os.path.exists(input_json_path):
        print(f"Error: File not found at path {input_json_path}")
        return

    """
    Группирует записи из JSON по списку префиксов или по первым 3 частям ключа
    и экспортирует каждую группу в отдельный .po файл с использованием polib.
    """

    # 1. ПОЛНЫЙ И ОЧИЩЕННЫЙ СПИСОК ИСКЛЮЧЕНИЙ
    EXCEPTIONS = [
        "SkillString_STR_SKILL_PC_ASSASSIN", "SkillString_STR_SKILL_PC_CHANTER",
        "SkillString_STR_SKILL_PC_CLERIC", "SkillString_STR_SKILL_PC_ELEMENTALIST",
        "SkillString_STR_SKILL_PC_GLADIATOR", "SkillString_STR_SKILL_PC_RANGER",
        "SkillString_STR_SKILL_PC_SORCERER", "SkillString_STR_SKILL_PC_TEMPLAR",
        "SkillAbnormalString", "SkillCondString", "SkillString",
        "AchievementString", "AnonymousNameData", "CurrencyInfo", "CutsceneSubtitle",
        "EnvObjData", "EventContentsString", "GatherSkill", "NpcTalk",
        "GuideData", "InputKeyMapping", "InputKeyText", "InventoryFilter",
        "NoteData", "PackageList", "Post", "QuestPart", "QuestString", "ServerName",
        "SkinMaterial", "SkinSet", "String_AttrStatName", "String_StatName",
        "String_STR", "String_UI", "TeleportArtifact", "TitleCategory",
        "Message", "PcSocialAction", "Tag", "Title", "TradeTab", "Wing", "Skin", "String"
    ]

    # Сортировка исключений по убыванию длины для корректного поиска (сначала длинные)
    EXCEPTIONS.sort(key=len, reverse=True)

    # 2. Загрузка данных из JSON
    if not os.path.exists(input_json_path):
        print(f"❌ Файл не найден: {input_json_path}")
        return

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при чтении JSON: {e}")
        return

    # 3. Подготовка регулярного выражения
    # Шаблон: ^(ДлинныйПрефикс|КороткийПрефикс)(_ или конец строки)
    escaped_exceptions = [re.escape(p) for p in EXCEPTIONS]
    prefix_search_pattern = r"^(" + "|".join(escaped_exceptions) + r")(?:" + re.escape(separator) + r"|$)"

    # 4. Категоризация данных
    categories = {}
    print(f"🔄 Начат анализ {len(data)} записей...")

    for item in data:
        key = item.get('Key', '')
        if not key:
            continue

        # Поиск совпадения с исключением
        match = re.match(prefix_search_pattern, key)

        if match:
            # Если нашли в исключениях
            prefix = match.group(1)
        else:
            # Стандартное правило: первые 3 элемента ключа
            key_parts = key.split(separator)
            if len(key_parts) >= 3:
                prefix = separator.join(key_parts[:3])
            else:
                # Если частей меньше 3, берем весь ключ или помечаем как uncategorized
                prefix = f"UNCATEGORIZED"

        if prefix not in categories:
            categories[prefix] = []

        categories[prefix].append(item)

    # 5. Экспорт в .po файлы с помощью polib
    output_dir = "po_categories"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    exported_files_count = 0
    total_entries_count = 0

    print(f"✅ Найдено {len(categories)} категорий. Создание PO-файлов...")

    for prefix, items in categories.items():
        # Создаем объект POFile
        po = polib.POFile()

        # Важно: добавляем метаданные, чтобы редакторы (Poedit) понимали кодировку
        po.metadata = {
            'Project-Id-Version': '1.0',
            'Report-Msgid-Bugs-To': '',
            'POT-Creation-Date': '',
            'PO-Revision-Date': '',
            'Last-Translator': '',
            'Language-Team': '',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }

        for item in items:
            # Извлекаем данные
            key = item.get('Key', '')
            original_text = item.get('Value', '')
            translated_text = item.get('Russian_Value', '')

            # Создаем запись
            entry = polib.POEntry(
                msgctxt=key,  # Контекст (Ключ)
                msgid=original_text,  # Оригинал
                msgstr=translated_text  # Перевод
            )

            # Добавляем в файл
            po.append(entry)
            total_entries_count += 1

        # Сохранение файла
        output_filename = os.path.join(output_dir, f"{prefix}.po")
        try:
            po.save(output_filename)
            exported_files_count += 1
            # Опционально: print(f"   -> Сохранен: {output_filename} ({len(items)} записей)")
        except Exception as e:
            print(f"❌ Ошибка сохранения {output_filename}: {e}")

    print(f"\n🎉 Готово! Создано файлов: {exported_files_count}.")
    print(f"📄 Всего записей обработано: {total_entries_count}.")
    print(f"📂 Папка вывода: {os.path.abspath(output_dir)}")