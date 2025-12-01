#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления API ключа CapSolver
Убирает ВСЕ пробелы и невидимые символы
"""

import sys
import io

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*70)
print("CapSolver API Key Fixer")
print("="*70)

# Читаем текущий ключ
try:
    with open("capsolver_config.txt", 'r', encoding='utf-8') as f:
        current_key = f.read()
except Exception as e:
    print(f"\n❌ Ошибка чтения файла: {e}")
    sys.exit(1)

print(f"\n[BEFORE] Current key:")
print(f"   Length: {len(current_key)} characters")
print(f"   Content: '{current_key}'")
print(f"   Repr: {repr(current_key)}")

# Убираем ВСЕ пробелы и невидимые символы
cleaned_key = ''.join(current_key.split())

print(f"\n[AFTER] Cleaned key:")
print(f"   Length: {len(cleaned_key)} characters")
print(f"   Content: '{cleaned_key}'")
print(f"   Repr: {repr(cleaned_key)}")

# Проверяем формат
if not cleaned_key.startswith("CAP-"):
    print(f"\n❌ Ключ не начинается с 'CAP-'")
    print(f"   Возможно, это неправильный ключ")
    print(f"\n💡 Скопируйте правильный API ключ:")
    print(f"   1. Зайдите: https://dashboard.capsolver.com/dashboard/overview")
    print(f"   2. Найдите 'API Key' (начинается с CAP-)")
    print(f"   3. Нажмите 'Copy'")
    print(f"   4. Вставьте сюда (БЕЗ пробелов):")

    new_key = input("\n   API Key: ").strip()
    cleaned_key = ''.join(new_key.split())

    if not cleaned_key.startswith("CAP-"):
        print(f"❌ Всё ещё неправильный формат!")
        sys.exit(1)

if len(cleaned_key) != 68:
    print(f"\n⚠️  ВНИМАНИЕ: Неправильная длина!")
    print(f"   Ожидается: 68 символов (CAP- + 64 hex)")
    print(f"   Получено: {len(cleaned_key)} символов")

    if len(cleaned_key) < 68:
        print(f"\n❌ Ключ слишком короткий - неполный!")
    else:
        print(f"\n⚠️  Ключ слишком длинный - лишние символы!")

# Сохраняем исправленный ключ
try:
    with open("capsolver_config.txt", 'w', encoding='utf-8') as f:
        f.write(cleaned_key)

    print(f"\n✓ Файл исправлен и сохранён!")
    print(f"   Новый ключ: {cleaned_key[:15]}...{cleaned_key[-10:]}")
    print(f"   Длина: {len(cleaned_key)} символов")

    # Проверяем что сохранилось правильно
    with open("capsolver_config.txt", 'r', encoding='utf-8') as f:
        saved_key = f.read()

    if saved_key == cleaned_key and len(saved_key) == 68:
        print(f"\n✓✓✓ УСПЕХ! Ключ сохранён правильно!")
        print(f"\nТеперь запустите: python test_capsolver_minimal.py")
    else:
        print(f"\n⚠️  Предупреждение: После сохранения длина изменилась")
        print(f"   Сохранено: {len(saved_key)} символов")

except Exception as e:
    print(f"\n❌ Ошибка сохранения: {e}")
    sys.exit(1)

print("="*70)
