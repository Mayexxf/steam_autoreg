#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook Account Creator Package
Автоматическое создание аккаунтов Microsoft Outlook с обходом детекции

Использование:
    python -m outlook.main
    python -m outlook.main --headless
    python -m outlook.main --proxy=user:pass:host:port
    python -m outlook.main --rotate-ip
"""

from .creator import OutlookCreator
from .config import HARDCODED_PROXY
from .browser import BrowserManager
from .captcha import CaptchaSolver
from .forms import FormFiller

__all__ = [
    'OutlookCreator',
    'BrowserManager',
    'CaptchaSolver',
    'FormFiller',
    'HARDCODED_PROXY'
]
__version__ = '2.0.0'
