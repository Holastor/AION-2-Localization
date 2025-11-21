#Requires -Version 3.0

$OutputEncoding = [System.Text.Encoding]::UTF8

# ----------------------------------------------------
# 1. КОНФИГУРАЦИЯ
# ----------------------------------------------------
$configFile = "aion2_path.cfg"
$downloadUrl = "https://github.com/Holastor/AION-2-Localization/raw/refs/heads/main/Localization%20pak%20file/pakchunk502000-Windows_9999_P.pak" 
$targetFilename = "pakchunk502000-Windows_9999_P.pak"
$targetSubpath = "Aion2\Content\Paks\L10N\Text\en-US"

# Русские тексты для консоли
$T_Title = "Запуск обновления локализации AION2 by - AkiX"
$T_ConfigEmpty = "Файл конфигурации пуст. Запрашиваем путь заново."
$T_PathFound = "✅ Найден сохраненный путь:"
$T_FirstRun = "⚠️ Это первый запуск скрипта."
$T_InputPrompt = "Укажите полный путь к корневой папке игры (например, C:\Games\AION2_TW)."
$T_PathInput = "Введите путь"
$T_PathError = "⛔️ Ошибка: Путь не может быть пустым. Попробуйте еще раз."
$T_PathSaved = "💾 Путь к игре сохранен в $configFile."
$T_CheckFolder = "`n⚙️ Проверка папки назначения:"
$T_FoldersOK = "✅ Папки существуют или успешно созданы."
$T_CriticalError = "❌ Критическая ошибка: Не удалось создать папку. Проверьте права доступа."
$T_DownloadStart = "`n🌐 Запуск скачивания:"
$T_DownloadSuccess = "`n🎉 Успех! Файл успешно скачан и обновлен."
$T_DownloadError = "`n❌ Ошибка при скачивании файла. Проверьте IP, URL и интернет-соединение."
$T_ExitPrompt = "Готово. Нажмите Enter для выхода..."

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "    $T_Title" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------
# 2. ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ПУТИ К ИГРЕ
# ----------------------------------------------------

function Get-GamePath {
    if (Test-Path $configFile) {
        # Читаем сохраненный путь (используем UTF8)
        $savedPath = Get-Content $configFile -First 1 -Encoding UTF8
        $savedPath = $savedPath.Trim()
        
        if (-not $savedPath) {
            Write-Warning $T_ConfigEmpty
            Remove-Item $configFile -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "$T_PathFound $savedPath" -ForegroundColor Green
            return $savedPath
        }
    }
    
    # Запрос пути у пользователя
    Write-Host ""
    Write-Host $T_FirstRun -ForegroundColor Yellow
    Write-Host $T_InputPrompt -ForegroundColor Yellow
    
    while ($true) {
        $path = Read-Host $T_PathInput
        $path = $path.Trim().Trim('"')
        
        if ($path) {
            # Сохраняем путь для будущих запусков
            $path | Out-File $configFile -Encoding UTF8
            Write-Host ""
            Write-Host $T_PathSaved -ForegroundColor Green
            return $path
        } else {
            Write-Host $T_PathError -ForegroundColor Red
        }
    }
}

# ----------------------------------------------------
# 3. ОСНОВНАЯ ЛОГИКА
# ----------------------------------------------------

$gamePath = Get-GamePath
if (-not $gamePath) {
    Read-Host $T_ExitPrompt | Out-Null
    exit
}

# Формируем полный путь
$targetDir = Join-Path $gamePath $targetSubpath
$targetFile = Join-Path $targetDir $targetFilename

Write-Host "$T_CheckFolder $targetDir" -ForegroundColor Yellow

# 1. Создание папок
try {
    New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
    Write-Host $T_FoldersOK -ForegroundColor Green
} catch {
    Write-Host $T_CriticalError -ForegroundColor Red
    Read-Host $T_ExitPrompt | Out-Null
    exit
}

# 2. Скачивание файла
Write-Host "$T_DownloadStart $targetFilename" -ForegroundColor Yellow
Write-Host "   Источник: $downloadUrl"
Write-Host "   Назначение: $targetFile"

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $targetFile -TimeoutSec 60
    
    Write-Host $T_DownloadSuccess -ForegroundColor Green

} catch {
    Write-Host $T_DownloadError -ForegroundColor Red
    Write-Host "   Сообщение об ошибке: $($_.Exception.Message)" -ForegroundColor Red
}

# ----------------------------------------------------
# 4. ЗАВЕРШЕНИЕ
# ----------------------------------------------------
Write-Host ""
Read-Host $T_ExitPrompt | Out-Null