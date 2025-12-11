#!/bin/bash

# ============================================================
# ВАЖНО: Переходим в директорию, где лежит этот скрипт
# ============================================================
cd "$(dirname "$0")" || exit

# Название вашего скрипта
PYTHON_SCRIPT="localization_tool.py"

# Очистка экрана для красоты
clear

echo "========================================================"
echo "          Localization Tool Launcher (macOS)"
echo "========================================================"

# ============================================================
# 1. ПРОВЕРКА НАЛИЧИЯ PYTHON 3
# ============================================================
echo "[Checking] Verifying Python 3 installation..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VER=$($PYTHON_CMD --version)
    echo "[OK] Found $PYTHON_VER"
else
    echo ""
    echo "[ERROR] Python 3 is not found on this system!"
    echo ""
    echo "Please install Python from the official website:"
    echo "https://www.python.org/downloads/"
    echo ""
    echo "Or run in terminal: brew install python"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# ============================================================
# 2. ПРОВЕРКА И УСТАНОВКА МОДУЛЕЙ
# ============================================================
echo ""
echo "[Checking] Verifying required libraries..."

MODULE_TO_CHECK="polib"

# Проверяем импорт
$PYTHON_CMD -c "import $MODULE_TO_CHECK" 2> /dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] Module '$MODULE_TO_CHECK' is not installed."
    echo ""
    # Читаем ввод пользователя (ключ -n 1 читает 1 символ)
    read -p "Do you want to install '$MODULE_TO_CHECK' now? (Y/N): " INSTALL_CHOICE
    echo "" # Перенос строки после ввода

    # Конвертируем в верхний регистр (совместимый способ)
    INSTALL_CHOICE=$(echo "$INSTALL_CHOICE" | tr '[:lower:]' '[:upper:]')

    if [[ "$INSTALL_CHOICE" == "Y" || "$INSTALL_CHOICE" == "YES" ]]; then
        echo "[Installing] Installing $MODULE_TO_CHECK..."

        # Используем --user для избежания ошибок прав доступа
        $PYTHON_CMD -m pip install --user $MODULE_TO_CHECK --break-system-packages 2>/dev/null || $PYTHON_CMD -m pip install --user $MODULE_TO_CHECK

        if [ $? -ne 0 ]; then
            echo ""
            echo "[ERROR] Failed to install the module."
            echo "Try running 'python3 -m pip install polib' manually in Terminal."
            read -p "Press Enter to exit..."
            exit 1
        fi
        echo "[OK] Module installed successfully."
    else
        echo ""
        echo "[STOP] Cannot run without '$MODULE_TO_CHECK'. Aborting."
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    echo "[OK] Module '$MODULE_TO_CHECK' is already installed."
fi

# ============================================================
# 3. ЗАПУСК СКРИПТА
# ============================================================
echo ""
echo "[Running] Executing $PYTHON_SCRIPT..."
echo "--------------------------------------------------------"
echo ""

if [ -f "$PYTHON_SCRIPT" ]; then
    $PYTHON_CMD "$PYTHON_SCRIPT"
else
    echo "[ERROR] The script '$PYTHON_SCRIPT' was not found in:"
    echo "$(pwd)"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "========================================================"
echo "[Done] Process finished. You can close this window."
# На macOS .command часто закрывает окно сразу после завершения,
# если не изменить настройки терминала, поэтому pause важен.
read -p "Press Enter to exit..."
