import os
import json
import re
import polib


def categorize_and_export_po():
    print("""
    ===================================================================
                      JSON to PO: Smart Categorization
    ===================================================================
    This script performs the following actions:

    1. Reads the source JSON file containing localization data.
    2. Analyzes keys and groups entries based on three priority rules:
       - Special Patterns: Extracts specific categories (e.g., Class Skills).
       - Prefix Exceptions: Groups by defined prefixes (e.g., AchievementString).
       - Standard Logic: Groups by the first 3 parts of the key.
    3. Exports each group into a separate .po file using polib.

    Results will be saved in the 'po_dictonaries' directory.
    ===================================================================
    """)
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
 # ПОЛНЫЙ СПИСОК ИСКЛЮЧЕНИЙ ИЗ ВАШЕГО КОДА
    EXCEPTIONS_ALL = [
        "AchievementString", "AnonymousNameData", "CurrencyInfo", "CutsceneSubtitle", "EnvObjData", "EventContentsString", "GatherSkill", "NpcTalk",
        "GuideData", "InputKeyMapping", "InputKeyText", "InventoryFilter", "NoteData", "PackageList", "Post", "QuestPart", "QuestString", "ServerName",
        "SkillAbnormalString", "SkillCondString", "SkillString_SkillString", 
        "SkillString_STR_SKILL_PC_ASSASSIN", "SkillString_STR_SKILL_PC_CHANTER", #<-- ЭТИ БУДУТ УДАЛЕНЫ
        "SkillString_STR_SKILL_PC_CLERIC", "SkillString_STR_SKILL_PC_ELEMENTALIST", "SkillString_STR_SKILL_PC_GLADIATOR", "SkillString_STR_SKILL_PC_RANGER",#<-- ЭТИ БУДУТ УДАЛЕНЫ
        "SkillString_STR_SKILL_PC_SORCERER", "SkillString_STR_SKILL_PC_TEMPLAR",  #<-- ЭТИ БУДУТ УДАЛЕНЫ
        "Skin", "PcSocialAction", "Message", "SkinMaterial", "SkinSet", "String_AttrStatName",
        "String_StatName", "String_STR", "String_UI", "TeleportArtifact", "Title", "TradeTab", "Tag", "TitleCategory", "Wing", "String"
    ]

    # 1. ШАБЛОНЫ ДЛЯ ГРУППИРОВКИ ПО ЧИСЛУ (НОВЫЙ БЛОК)
    # Формат: (Префикс, Суффикс, Имя категории)
    PATTERN_EXCEPTIONS = [
        ("SkillString_STR_SKILL_PC_ASSASSIN", "_skill_name", "SkillString_ASSASSIN_SKILLS"),
        ("SkillString_STR_SKILL_PC_CHANTER", "_skill_name", "SkillString_CHANTER_SKILLS"),
        ("SkillString_STR_SKILL_PC_CLERIC", "_skill_name", "SkillString_CLERIC_SKILLS"),
        ("SkillString_STR_SKILL_PC_ELEMENTALIST", "_skill_name", "SkillString_ELEMENTALIST_SKILLS"),
        ("SkillString_STR_SKILL_PC_GLADIATOR", "_skill_name", "SkillString_GLADIATOR_SKILLS"),
        ("SkillString_STR_SKILL_PC_RANGER", "_skill_name", "SkillString_RANGER_SKILLS"),
        ("SkillString_STR_SKILL_PC_SORCERER", "_skill_name", "SkillString_SORCERER_SKILLS"),
        ("SkillString_STR_SKILL_PC_TEMPLAR", "_skill_name", "SkillString_TEMPLAR_SKILLS"),
        ("SkillString_STR_SKILL_PC_ASSASSIN", "_skill_desc_effect", "SkillString_ASSASSIN_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_CHANTER", "_skill_desc_effect", "SkillString_CHANTER_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_CLERIC", "_skill_desc_effect", "SkillString_CLERIC_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_ELEMENTALIST", "_skill_desc_effect", "SkillString_ELEMENTALIST_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_GLADIATOR", "_skill_desc_effect", "SkillString_GLADIATOR_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_RANGER", "_skill_desc_effect", "SkillString_RANGER_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_SORCERER", "_skill_desc_effect", "SkillString_SORCERER_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_TEMPLAR", "_skill_desc_effect", "SkillString_TEMPLAR_skill_desc_effect"),
        ("SkillString_STR_SKILL_PC_ASSASSIN", "_skill_spec_effect", "SkillString_ASSASSIN_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_CHANTER", "_skill_spec_effect", "SkillString_CHANTER_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_CLERIC", "_skill_spec_effect", "SkillString_CLERIC_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_ELEMENTALIST", "_skill_spec_effect", "SkillString_ELEMENTALIST_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_GLADIATOR", "_skill_spec_effect", "SkillString_GLADIATOR_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_RANGER", "_skill_spec_effect", "SkillString_RANGER_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_SORCERER", "_skill_spec_effect", "SkillString_SORCERER_skill_spec_effect"),
        ("SkillString_STR_SKILL_PC_TEMPLAR", "_skill_spec_effect", "SkillString_TEMPLAR_skill_spec_effect"),
        # Добавьте другие числовые шаблоны сюда
    ]
    # Мы удаляем элементы, которые обрабатываются в PATTERN_EXCEPTIONS, 
    # чтобы избежать их дублирования или обработки по правилу первых 3 слов.
    pattern_prefixes = [p[0] for p in PATTERN_EXCEPTIONS]
    EXCEPTIONS = [p for p in EXCEPTIONS_ALL if p not in pattern_prefixes]

    # 3. Сортировка оставшихся исключений по убыванию длины
    EXCEPTIONS.sort(key=len, reverse=True)
    
    # 4. Компиляция шаблона поиска префиксов для ОСНОВНЫХ ИСКЛЮЧЕНИЙ
    prefix_search_pattern = r"^(" + "|".join(re.escape(p) for p in EXCEPTIONS) + r")(?:" + re.escape(separator) + r"|$)"
    prefix_search_compiled = re.compile(prefix_search_pattern)
    
    # 5. Категоризация данных
    categories = {}
    
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при загрузке JSON: {e}")
        return
    
    print(f"🔄 Начат анализ {len(data)} записей...")

    for item in data:
        key = item.get('Key', '')
        prefix = None
        
        # 5.1. ЛОГИКА 1: Проверка на числовой шаблон (ВЫСШИЙ ПРИОРИТЕТ)
        for pattern_prefix, pattern_suffix, category_name in PATTERN_EXCEPTIONS:
            # Строим шаблон: ^Prefix_(\d+)_Suffix$
            dynamic_pattern_str = re.escape(pattern_prefix) + re.escape(separator) + r"(\d+)" + re.escape(pattern_suffix) + r"$"
            dynamic_pattern = re.compile(dynamic_pattern_str)
            
            if dynamic_pattern.match(key):
                prefix = category_name # Используем заданное имя категории
                break # Нашли соответствие, переходим к следующему Key

        # 5.2. ЛОГИКА 2: Проверка на стандартное исключение
        if prefix is None:
            match = prefix_search_compiled.match(key)
            
            if match:
                prefix = match.group(1) # Берем совпавший префикс
            else:
                # 5.3. ЛОГИКА 3: Стандартное правило (первые 3 элемента)
                key_parts = key.split(separator)
                prefix = separator.join(key_parts[:3]) if len(key_parts) >= 3 else f"UNCATEGORIZED_{key}"
                
        # 5.4. Добавляем элемент в соответствующую категорию
        if prefix not in categories:
            categories[prefix] = []
        
        categories[prefix].append(item)

    # 6. Экспорт каждой категории в отдельный PO-файл
    # while True:
    #     dictmode = input(
    #         "Вы создаете словарь для перевода или обновляете локализацию новыми строками?\n введите цифру описывающею директории для экспорта словарей: \n 1-po_dictonaries\n 2-po_update\nвведите цифру: ")
    #     match dictmode:
    #         case "1":
    #             output_dir = "po_dictonaries"
    #         case "2":
    #             output_dir = "po_update"
    #         case _:
    #             print("\nIncorrect mode. Please enter 1 or 2\n")
    #             continue
    #     break
    output_dir = "po_dictonaries"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # output_dir = "po_categories"
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    exported_count = 0
    total_entries = 0

    print(f"✅ Найдено {len(categories)} уникальных категорий. Начало экспорта...")

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
            translated_text = item.get('Localization_Value', '')

            # Создаем запись
            entry = polib.POEntry(
                msgctxt=key,  # Контекст (Ключ)
                msgid=original_text,  # Оригинал
                msgstr=translated_text  # Перевод
            )

            # Добавляем в файл
            po.append(entry)
            total_entries += 1

        # Сохранение файла
        output_filename = os.path.join(output_dir, f"{prefix}.po")
        try:
            po.save(output_filename)
            exported_count += 1
            print(f"   -> Экспортировано {len(items)} записей в: {os.path.basename(output_filename)}")
        except Exception as e:
            print(f"❌ Ошибка при экспорте PO-файла {output_filename}: {e}")

    print(f"\n🎉 Категоризация завершена. Создано {exported_count} файлов ({total_entries} записей) в '{output_dir}'.")
