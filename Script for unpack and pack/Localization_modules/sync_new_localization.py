import os
import json
import re
import polib

# ==================================================================================
# 1. НАСТРОЙКИ И ПРАВИЛА ГРУППИРОВКИ (Ваш список исключений)
# ==================================================================================

# Папки
INPUT_DICT_DIR = "po_dictonaries"  # Откуда берем старые переводы
OUTPUT_DIR = "po_comparison"  # Куда кладем результат

EXCEPTIONS_ALL = [
    "AchievementString", "AnonymousNameData", "CurrencyInfo", "CutsceneSubtitle", "EnvObjData", "EventContentsString",
    "GatherSkill", "NpcTalk",
    "GuideData", "InputKeyMapping", "InputKeyText", "InventoryFilter", "NoteData", "PackageList", "Post", "QuestPart",
    "QuestString", "ServerName",
    "SkillAbnormalString", "SkillCondString", "SkillString_SkillString",
    "SkillString_STR_SKILL_PC_ASSASSIN", "SkillString_STR_SKILL_PC_CHANTER",
    "SkillString_STR_SKILL_PC_CLERIC", "SkillString_STR_SKILL_PC_ELEMENTALIST", "SkillString_STR_SKILL_PC_GLADIATOR",
    "SkillString_STR_SKILL_PC_RANGER",
    "SkillString_STR_SKILL_PC_SORCERER", "SkillString_STR_SKILL_PC_TEMPLAR", "Skin", "PcSocialAction", "Message",
    "SkinMaterial", "SkinSet", "String_AttrStatName",
    "String_StatName", "String_STR", "String_UI", "TeleportArtifact", "Title", "TradeTab", "Tag", "TitleCategory",
    "Wing", "String"
]

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
]

# Компиляция шаблонов
pattern_prefixes = [p[0] for p in PATTERN_EXCEPTIONS]
EXCEPTIONS = [p for p in EXCEPTIONS_ALL if p not in pattern_prefixes]
EXCEPTIONS.sort(key=len, reverse=True)
SEPARATOR = '_'
prefix_search_pattern = r"^(" + "|".join(re.escape(p) for p in EXCEPTIONS) + r")(?:" + re.escape(SEPARATOR) + r"|$)"
prefix_search_compiled = re.compile(prefix_search_pattern)


def get_category_for_key(key):
    """Определяет имя файла (категорию) для ключа."""
    # 1. Числовые шаблоны
    for pattern_prefix, pattern_suffix, category_name in PATTERN_EXCEPTIONS:
        dynamic_pattern_str = re.escape(pattern_prefix) + re.escape(SEPARATOR) + r"(\d+)" + re.escape(
            pattern_suffix) + r"$"
        if re.match(dynamic_pattern_str, key):
            return category_name
    # 2. Исключения (префиксы)
    match = prefix_search_compiled.match(key)
    if match:
        return match.group(1)
    # 3. Стандарт (3 слова)
    key_parts = key.split(SEPARATOR)
    return SEPARATOR.join(key_parts[:3]) if len(key_parts) >= 3 else f"UNCATEGORIZED_{key}"


# ==================================================================================
# 2. ФУНКЦИИ СРАВНЕНИЯ
# ==================================================================================

def load_existing_translations(folder_path):
    """Читает PO файлы и сохраняет переводы в словарь."""
    database = {}  # { 'Key': {'msgid': 'Eng', 'msgstr': 'Rus'} }
    print(f"📥 Чтение словарей из '{folder_path}'...")

    if not os.path.exists(folder_path):
        print(f"⚠️ Папка {folder_path} не найдена. Будут созданы новые файлы.")
        return database

    files_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".po"):
            filepath = os.path.join(folder_path, filename)
            try:
                po = polib.pofile(filepath)
                for entry in po:
                    database[entry.msgctxt] = {
                        'msgid': entry.msgid,
                        'msgstr': entry.msgstr
                    }
                files_count += 1
            except Exception as e:
                print(f"❌ Ошибка файла {filename}: {e}")

    print(f"📊 Загружено {len(database)} записей из {files_count} файлов.")
    return database


def process_sync():
    print("""
    ===================================================================
                      JSON <-> PO: Smart Synchronization
    ===================================================================
    This script updates your existing PO dictionaries with new data from JSON:

    1. Loads existing translations from the 'po_dictonaries' folder.
    2. Compares keys from the new JSON file against the existing database.
    3. Applies synchronization logic:
       - [NEW] Key did not exist -> Adds entry with empty translation.
       - [CHANGED] Source English text changed -> Resets translation, marks as 'fuzzy', and saves the old translation in comments.
       - [SAME] Source text unchanged -> Preserves the existing translation.
    4. Categorizes and saves updated files to 'po_comparison'.

    This ensures your translations are carried over while highlighting what needs re-translation.
    ===================================================================
    """)
    input_json_path = input("Введите путь к JSON файлу (источник новых данных): ")
    if not os.path.exists(input_json_path):
        print(f"❌ Файл не найден: {input_json_path}")
        return

    # 1. Загружаем старые переводы
    old_db = load_existing_translations(INPUT_DICT_DIR)

    # 2. Загружаем новый JSON
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return

    categories = {}  # Структура: {'filename': [POEntry, POEntry...]}
    stats = {'new': 0, 'changed': 0, 'unchanged': 0}

    print("🔄 Сравнение JSON и текущих словарей...")

    for item in new_data:
        key = item.get('Key')
        new_english_value = item.get('Value', '')  # Новый оригинал из JSON

        if not key:
            continue

        # Определяем, в какой файл это должно попасть
        category = get_category_for_key(key)
        if category not in categories:
            categories[category] = []

        # Создаем новую запись
        entry = polib.POEntry(msgctxt=key, msgid=new_english_value)

        # ЛОГИКА СРАВНЕНИЯ
        if key in old_db:
            old_data = old_db[key]
            old_english = old_data['msgid']
            old_russian = old_data['msgstr']

            if old_english != new_english_value:
                # 🟡 ИЗМЕНЕНИЕ: Оригинал (EN) изменился
                # Сбрасываем перевод, старый пишем в коммент
                entry.msgstr = ""
                entry.tcomment = f"Old translation was: {old_russian}"
                entry.flags.append('fuzzy')  # Помечаем как неточный
                stats['changed'] += 1
            else:
                # 🟢 БЕЗ ИЗМЕНЕНИЙ: Оригинал тот же
                # Просто копируем существующий перевод
                entry.msgstr = old_russian
                stats['unchanged'] += 1
        else:
            # 🔵 НОВЫЙ: Ключа раньше не было
            entry.msgstr = ""  # Перевода нет
            stats['new'] += 1

        categories[category].append(entry)

    # 3. Сохранение результатов
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"💾 Сохранение файлов в '{OUTPUT_DIR}'...")

    saved_count = 0
    for cat_name, entries in categories.items():
        po = polib.POFile()
        po.metadata = {
            'Project-Id-Version': '1.0',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }

        for entry in entries:
            po.append(entry)

        output_filename = os.path.join(OUTPUT_DIR, f"{cat_name}.po")
        try:
            po.save(output_filename)
            saved_count += 1
        except Exception as e:
            print(f"❌ Ошибка сохранения {output_filename}: {e}")

    print("\n" + "=" * 40)
    print(f"🎉 Готово! Обработано {len(new_data)} ключей из JSON.")
    print(f"📂 Создано файлов: {saved_count}")
    print(f"📈 Статистика:")
    print(f"   ➕ Новых строк (пустой перевод): {stats['new']}")
    print(f"   ⚠️ Изменен оригинал (старый перевод в комментарии): {stats['changed']}")
    print(f"   ✅ Без изменений (перевод сохранен): {stats['unchanged']}")
    print("=" * 40)
    print(f"Теперь содержимое папки '{OUTPUT_DIR}' является актуальной версией.")
