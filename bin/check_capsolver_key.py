#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Читаем текущий ключ
try:
    with open("capsolver_config.txt", 'r', encoding='utf-8') as f:
        current_key = f.read()
except Exception as e:
    print(f"\n Ошибка чтения файла: {e}")
    sys.exit(1)

# Убираем ВСЕ пробелы и невидимые символы
cleaned_key = ''.join(current_key.split())

# Проверяем формат
if not cleaned_key.startswith("CAP-"):
    new_key = input("\n   API Key: ").strip()
    cleaned_key = ''.join(new_key.split())

    if not cleaned_key.startswith("CAP-"):
        sys.exit(1)

# Сохраняем исправленный ключ
try:
    with open("capsolver_config.txt", 'w', encoding='utf-8') as f:
        f.write(cleaned_key)

    # Проверяем что сохранилось правильно
    with open("capsolver_config.txt", 'r', encoding='utf-8') as f:
        saved_key = f.read()

except Exception as e:
    print(f"\n Ошибка сохранения: {e}")
    sys.exit(1)

print("="*70)
