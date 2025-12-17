#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Recorder - записывает реальные движения мыши пользователя
Использует pynput для перехвата событий на уровне ОС
"""

import time
import json
import threading
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MouseEvent:
    """Событие мыши"""
    timestamp: float  # Время события
    x: int  # Координата X
    y: int  # Координата Y
    event_type: str  # 'move', 'click', 'scroll'
    button: Optional[str] = None  # 'left', 'right', 'middle' для кликов
    scroll_dx: int = 0  # Горизонтальный скролл
    scroll_dy: int = 0  # Вертикальный скролл


class MouseRecorder:
    """
    Записывает движения мыши пользователя в реальном времени
    """

    def __init__(self):
        self.events: List[MouseEvent] = []
        self.is_recording = False
        self.start_time = None
        self.listener = None
        self._lock = threading.Lock()

    def start_recording(self):
        """Начинает запись движений мыши"""
        try:
            from pynput import mouse
        except ImportError:
            raise ImportError(
                "pynput не установлен. Установите: pip install pynput"
            )

        with self._lock:
            self.events = []
            self.is_recording = True
            self.start_time = time.time()

        print("[MOUSE RECORDER] 🎙️  Запись началась!")
        print("[MOUSE RECORDER] Двигайте мышью как обычно")
        print("[MOUSE RECORDER] Нажмите Ctrl+C или вызовите stop_recording() для остановки")

        def on_move(x, y):
            if self.is_recording:
                event = MouseEvent(
                    timestamp=time.time() - self.start_time,
                    x=x,
                    y=y,
                    event_type='move'
                )
                with self._lock:
                    self.events.append(event)

        def on_click(x, y, button, pressed):
            if self.is_recording and pressed:  # Только нажатия
                button_name = button.name if hasattr(button, 'name') else str(button)
                event = MouseEvent(
                    timestamp=time.time() - self.start_time,
                    x=x,
                    y=y,
                    event_type='click',
                    button=button_name
                )
                with self._lock:
                    self.events.append(event)

        def on_scroll(x, y, dx, dy):
            if self.is_recording:
                event = MouseEvent(
                    timestamp=time.time() - self.start_time,
                    x=x,
                    y=y,
                    event_type='scroll',
                    scroll_dx=dx,
                    scroll_dy=dy
                )
                with self._lock:
                    self.events.append(event)

        # Создаем listener в отдельном потоке
        self.listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.listener.start()

    def stop_recording(self) -> int:
        """
        Останавливает запись

        Returns:
            int: Количество записанных событий
        """
        with self._lock:
            self.is_recording = False

        if self.listener:
            self.listener.stop()
            self.listener = None

        events_count = len(self.events)
        print(f"\n[MOUSE RECORDER] ⏹️  Запись остановлена!")
        print(f"[MOUSE RECORDER] Записано событий: {events_count}")

        return events_count

    def save_to_file(self, filepath: str):
        """
        Сохраняет записанные события в JSON файл

        Args:
            filepath: Путь к файлу для сохранения
        """
        data = {
            'version': '1.0',
            'total_events': len(self.events),
            'duration': self.events[-1].timestamp if self.events else 0,
            'events': [asdict(event) for event in self.events]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"[MOUSE RECORDER] 💾 Сохранено в: {filepath}")

    def get_events(self) -> List[MouseEvent]:
        """Возвращает записанные события"""
        with self._lock:
            return self.events.copy()

    def get_summary(self) -> Dict:
        """Возвращает статистику записи"""
        with self._lock:
            moves = sum(1 for e in self.events if e.event_type == 'move')
            clicks = sum(1 for e in self.events if e.event_type == 'click')
            scrolls = sum(1 for e in self.events if e.event_type == 'scroll')
            duration = self.events[-1].timestamp if self.events else 0

            return {
                'total_events': len(self.events),
                'moves': moves,
                'clicks': clicks,
                'scrolls': scrolls,
                'duration': duration
            }


class MouseRecordingSession:
    """
    Контекстный менеджер для записи движений мыши

    Пример использования:
        with MouseRecordingSession(duration=10) as session:
            # Двигайте мышью в течение 10 секунд
            pass
        session.save_to_file('recording.json')
    """

    def __init__(self, duration: Optional[float] = None):
        """
        Args:
            duration: Длительность записи в секундах (None = бесконечно)
        """
        self.recorder = MouseRecorder()
        self.duration = duration
        self._timer = None

    def __enter__(self):
        self.recorder.start_recording()

        if self.duration:
            def stop_after_duration():
                time.sleep(self.duration)
                self.recorder.stop_recording()

            self._timer = threading.Thread(target=stop_after_duration, daemon=True)
            self._timer.start()

        return self.recorder

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.recorder.is_recording:
            self.recorder.stop_recording()


def load_recording(filepath: str) -> List[MouseEvent]:
    """
    Загружает запись из файла

    Args:
        filepath: Путь к файлу с записью

    Returns:
        List[MouseEvent]: Список событий мыши
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    events = []
    for event_data in data['events']:
        events.append(MouseEvent(**event_data))

    return events


# Примеры использования
if __name__ == '__main__':
    import sys

    print("="*70)
    print("MOUSE RECORDER - Запись движений мыши")
    print("="*70)

    print("\nВыберите режим:")
    print("1. Записать 10 секунд движений")
    print("2. Записать до нажатия Ctrl+C")

    choice = input("\nВыбор (1/2): ").strip()

    if choice == '1':
        print("\n[INFO] Запись 10 секунд...")
        print("[INFO] Начните двигать мышью СЕЙЧАС!")

        with MouseRecordingSession(duration=10) as recorder:
            # Ждем завершения записи
            time.sleep(10.5)

        summary = recorder.get_summary()
        print(f"\n[SUMMARY] Записано:")
        print(f"  - Движений: {summary['moves']}")
        print(f"  - Кликов: {summary['clicks']}")
        print(f"  - Скроллов: {summary['scrolls']}")
        print(f"  - Длительность: {summary['duration']:.2f}s")

        filename = f"mouse_recording_{int(time.time())}.json"
        recorder.save_to_file(filename)

    elif choice == '2':
        recorder = MouseRecorder()
        recorder.start_recording()

        try:
            print("\n[INFO] Двигайте мышью...")
            print("[INFO] Нажмите Ctrl+C для остановки\n")
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            recorder.stop_recording()

            summary = recorder.get_summary()
            print(f"\n[SUMMARY] Записано:")
            print(f"  - Движений: {summary['moves']}")
            print(f"  - Кликов: {summary['clicks']}")
            print(f"  - Скроллов: {summary['scrolls']}")
            print(f"  - Длительность: {summary['duration']:.2f}s")

            filename = f"mouse_recording_{int(time.time())}.json"
            recorder.save_to_file(filename)

    else:
        print("Неверный выбор")
        sys.exit(1)

    print("\n[DONE] Запись завершена!")
