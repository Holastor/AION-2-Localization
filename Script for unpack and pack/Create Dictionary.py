import json
import os
import re
import polib
import glob
from tkinter import filedialog, messagebox

def format_po_string(text):
	"""Форматирует текст для записи в PO-файл, экранируя спецсимволы."""
	text = str(text).strip()
	text = text.replace('\\', '\\\\')
	text = text.replace('"', '\\"')
	text = text.replace('\n', '\\n')
	return text

def get_po_file(po_path):
	"""Создает новый PO-файл с стандартным заголовком."""
	po = polib.POFile()
	po.metadata = {
		'Project-Id-Version': 'Aion2 Localization',
		'Report-Msgid-Bugs-To': '',
		'POT-Creation-Date': '2025-01-01 00:00+0000',
		'PO-Revision-Date': 'YEAR-MO-DA HO:MI+ZONE',
		'Last-Translator': 'FULL NAME <EMAIL@ADDRESS>',
		'Language-Team': 'Russian',
		'Language': 'ru',
		'MIME-Version': '1.0',
		'Content-Type': 'text/plain; charset=UTF-8',
		'Content-Transfer-Encoding': '8bit',
	}
	return po
def categorize_and_export_po(input_json_path, output_dir="po_categories", separator='_'):
	"""
	Группирует записи из JSON по заданному сложному списку префиксов 
	и экспортирует каждую группу в отдельный .po файл.
	"""
	
	# ПОЛНЫЙ И ОЧИЩЕННЫЙ СПИСОК ИСКЛЮЧЕНИЙ
	# NOTE: Исключения упорядочены по длине, чтобы при поиске совпадал максимально длинный префикс.
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
	
	# 1. Сортировка исключений по убыванию длины для поиска максимально длинного префикса
	EXCEPTIONS.sort(key=len, reverse=True)
	
	# 2. Загрузка данных из JSON
	try:
		with open(input_json_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
	except Exception as e:
		print(f"❌ Ошибка при загрузке JSON: {e}")
		return
	
	# 3. Создание шаблона поиска префиксов (для всех исключений)
	# Шаблон: ^(ДлинныйПрефикс|КороткийПрефикс)(_ или конец строки)
	prefix_search_pattern = r"^(" + "|".join(re.escape(p) for p in EXCEPTIONS) + r")(?:" + re.escape(separator) + r"|$)"
	
	# 4. Категоризация данных
	categories = {}
	
	print(f"🔄 Начат анализ {len(data)} записей...")
	
	for item in data:
		key = item.get('Key', '')
		
		# 4.1. Поиск совпадения с исключением (максимально длинным)
		match = re.match(prefix_search_pattern, key)
		
		if match:
			prefix = match.group(1) # Берем совпавший префикс (Message_MSG, SkillString_STR_SKILL_PC_ASSASSIN и т.д.)
		else:
			# 4.2. Стандартное правило: первые 3 элемента
			key_parts = key.split(separator)
			prefix = separator.join(key_parts[:3]) if len(key_parts) >= 3 else f"UNCATEGORIZED_{key}"
			
		# 4.3. Добавляем элемент в соответствующую категорию
		if prefix not in categories:
			categories[prefix] = []
		
		categories[prefix].append(item)
	
	# 5. Экспорт каждой категории в отдельный PO-файл
	
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
		
	exported_count = 0
	total_entries = 0
	
	print(f"✅ Найдено {len(categories)} уникальных категорий. Начало экспорта...")
	
	for prefix, items in categories.items():
		output_filename = os.path.join(output_dir, f"{prefix}.po")
		
		po = get_po_file(output_filename) # Создаем новый PO-файл
		
		for item in items:
			# Создаем новую запись polib.POEntry
			
			# Если Russian_value пуст, msgstr будет пустым, что стандартно для PO.
			new_entry = polib.POEntry(
				msgctxt=item.get('Key', ''),
				msgid=item.get('Value', ''),
				msgstr=item.get('Russian_Value', '')
			)
			po.append(new_entry)
			total_entries += 1
		
		try:
			po.save(output_filename)
			exported_count += 1
			print(f"   -> Экспортировано {len(items)} записей в: {os.path.basename(output_filename)}")
		except Exception as e:
			print(f"❌ Ошибка при экспорте PO-файла {output_filename}: {e}")
	
	print(f"\n🎉 Категоризация завершена. Создано {exported_count} файлов ({total_entries} записей) в '{output_dir}'.")
	
def combine_po_files(input_directory, output_file_path):
	"""
	Находит и объединяет все .po файлы в заданной директории в один мастер-файл.
	УВЕЛИЧЕНИЕ СКОРОСТИ: Использован Set для проверки дубликатов.
	"""
	
	master_po = polib.POFile()
	
	# 1. Поиск файлов
	search_pattern = os.path.join(input_directory, '**', '*.po')
	all_files = glob.glob(search_pattern, recursive=True)
	
	if not all_files:
		messagebox.showerror("Ошибка", f"Файлы .po не найдены в директории: {input_directory}")
		return
	
	print(f"✅ Найдено {len(all_files)} файлов для объединения.")
	added_entries_count = 0
	
	# --- ОПТИМИЗАЦИЯ СКОРОСТИ: Набор существующих контекстов ---
	# Храним все msgctxt в наборе для проверки дубликатов за O(1)
	existing_contexts = set()
	# ------------------------------------------------------------
	
	# 2. Загрузка и объединение записей
	for file_path in all_files:
		try:
			po_part = polib.pofile(file_path)
			
			# Если это первый файл, копируем его метаданные в мастер-файл
			if not master_po.metadata:
				master_po.metadata = po_part.metadata
				
			# Добавляем записи
			for entry in po_part:
				# Пропускаем записи-заголовки
				if entry.msgid == '':
					continue
					
				context = entry.msgctxt.strip() if entry.msgctxt else ''
				
				# ИСПРАВЛЕНИЕ: Проверка дубликатов с использованием Set
				if context not in existing_contexts:
					master_po.append(entry)
					existing_contexts.add(context) # Добавляем новый ключ в набор
					added_entries_count += 1
			
			print(f"   + Добавлено записей из: {os.path.basename(file_path)}")
			
		except Exception as e:
			print(f"❌ Ошибка при обработке файла {os.path.basename(file_path)}: {e}")
			messagebox.showwarning("Ошибка файла", f"Проблема с файлом {os.path.basename(file_path)}. Пропущен.")
			continue
	
	# 3. Сохранение финального мастер-файла
	if added_entries_count > 0:
		try:
			master_po.save(output_file_path)
			messagebox.showinfo(
				"Успех", 
				f"Объединение завершено!\nВсего записей добавлено: {added_entries_count}"
			)
			print("\n--- Результат ---")
			print(f"🎉 Объединение успешно завершено. Файл сохранен как: {output_file_path}")
			print(f"📊 Всего записей в мастер-файле: {added_entries_count}")
		except Exception as e:
			messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить мастер-файл: {e}")
	else:
		messagebox.showwarning("Предупреждение", "Не найдено ни одной записи для сохранения.")

def combine_po():
	INPUT_DIR = "po_categories" 
	
	# Имя выходного мастер-файла
	OUTPUT_MASTER_FILE = "master_localization.po"
	combine_po_files(INPUT_DIR, OUTPUT_MASTER_FILE)

def categorize_and_split_json():
	# Ввод файла от пользователя
	INPUT_JSON_PATH = input("Введите путь или имя JSON файла для упаковки: ")
	
	# 1. Запуск упаковщика
	categorize_and_export_po(INPUT_JSON_PATH)
	
if __name__ == '__main__':
	print("--- ИНСТРУМЕНТ ЛОКАЛИЗАЦИИ AION2 ---")
	mode = input("Выберите режим (1-categorize_and_split_json, 2-combine_po): ")
	
	if mode == "1":
		categorize_and_split_json()
	elif mode =="2":
		combine_po()
	# elif mode =="3":
	# 	# potojson()
	# elif mode =="4":
	# 	# poupdate()
	# # elif mode =="5":
	# #     mergejson()        
	else:
		print("Неверный режим. Пожалуйста, введите 1, 2, 3, 4 или 5.")