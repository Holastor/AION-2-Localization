import os
import json
import requests

# ----------------------------------------------------
# 1. КОНФИГУРАЦИЯ
# ----------------------------------------------------
CONFIG_FILE = "aion2_path.json"
DOWNLOAD_URL = "https://github.com/Holastor/AION-2-Localization/raw/refs/heads/main/Localization%20pak%20file/pakchunk502000-Windows_9999_P.pak"
TARGET_FILENAME = "pakchunk502000-Windows_9999_P.pak"
# Относительный путь, куда должен быть помещен файл внутри папки игры
TARGET_SUBPATH = os.path.join("Aion2", "Content", "Paks", "L10N", "Text", "en-US")

def load_game_path():
    """Загружает сохраненный путь к игре из JSON-файла."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("game_path")
        except (IOError, json.JSONDecodeError):
            print("❌ Ошибка: Не удалось прочитать файл конфигурации. Начнем заново.")
            os.remove(CONFIG_FILE)
            return None
    return None

def save_game_path(path):
    """Сохраняет путь к игре в JSON-файл."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"game_path": path}, f, indent=4, ensure_ascii=False)
        print(f"💾 Путь к игре сохранен в {CONFIG_FILE}.")
    except Exception as e:
        print(f"❌ Ошибка при сохранении пути: {e}")

def get_game_path(saved_path):
    """Запрашивает путь у пользователя, если он не сохранен."""
    if saved_path:
        print(f"✅ Найден сохраненный путь: {saved_path}")
        return saved_path
    
    print("\n⚠️ Это первый запуск скрипта.")
    print("   Укажите полный путь к корневой папке игры (например, C:\\Games\\AION2_TW).")
    
    while True:
        # Используем input() для чистого ввода
        path = input("Введите путь: ").strip().strip('"')
        
        if path:
            # Преобразуем введенный путь в нормализованный формат Windows
            path = os.path.normpath(path)
            save_game_path(path)
            return path
        else:
            print("⛔️ Ошибка: Путь не может быть пустым. Попробуйте еще раз.")

def download_and_update(game_path):
    """Скачивает файл локализации и помещает его в целевую папку."""
    
    # Формируем полный путь к папке назначения
    target_dir = os.path.join(game_path, TARGET_SUBPATH)
    target_file = os.path.join(target_dir, TARGET_FILENAME)

    print(f"\n⚙️ Проверка папки назначения: {target_dir}")
    
    # 1. Создание папок, если они не существуют
    try:
        os.makedirs(target_dir, exist_ok=True)
        print("✅ Папки существуют или успешно созданы.")
    except OSError as e:
        print(f"❌ Критическая ошибка: Не удалось создать папку. {e}")
        print(f"   Проверьте права доступа или путь к игре: {game_path}")
        return

    # 2. Скачивание файла
    print(f"\n🌐 Запуск скачивания: {TARGET_FILENAME}")
    print(f"   Назначение: {target_file}")
    
    try:
        # Используем requests для скачивания
        response = requests.get(DOWNLOAD_URL, stream=True)
        response.raise_for_status() # Вызывает ошибку, если код ответа 4xx или 5xx

        # Запись файла по частям
        with open(target_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("\n🎉 Успех! Файл успешно скачан и обновлен.")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Ошибка при скачивании файла: {e}")
        print("   Проверьте интернет-соединение или URL-адрес.")
    except IOError as e:
        print(f"\n❌ Ошибка при записи файла: {e}")
        print("   Проверьте права доступа к папке игры.")

def main():
    """Основная функция программы."""
    print("=======================================================")
    print("    AION 2 TW Localization Updater (Python)")
    print("=======================================================")

    # 1. Получаем/запрашиваем путь к игре
    saved_path = load_game_path()
    game_path = get_game_path(saved_path)

    if game_path:
        # 2. Скачиваем и обновляем
        download_and_update(game_path)
    
    input("\nГотово. Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()