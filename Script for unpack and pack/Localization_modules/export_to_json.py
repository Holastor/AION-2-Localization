import json

def export_to_json(data, filename="output_data.json"):
    """Экспортирует список словарей в JSON-файл."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Данные успешно экспортированы в файл: {filename}")
        print(f"   Объектов экспортировано: {len(data)}")
    except Exception as e:
        print(f"\n❌ Ошибка при экспорте в JSON: {e}")

