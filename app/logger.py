"""
Multi-Channel Logger Module for DLRS Data Extractor Pro
Manages isolated loggers for System, Downloads, OCR, and Errors.
"""

import os
import logging
from typing import Callable, Optional

class GUIHandler(logging.Handler):
    """Custom logging handler to forward logs to GUI live log listener."""
    def __init__(self, callback: Optional[Callable[[str, str], None]] = None):
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord):
        if self.callback:
            msg = self.format(record)
            level = record.levelname
            try:
                self.callback(msg, level)
            except Exception:
                pass

class LogManager:
    """Central manager for multi-channel logging."""
    _initialized = False
    _loggers = {}
    _gui_handler = None

    @classmethod
    def setup_loggers(cls, log_dir: str = "./Output/Logs", log_level: str = "INFO", gui_callback: Optional[Callable[[str, str], None]] = None):
        os.makedirs(log_dir, exist_ok=True)
        level = getattr(logging, log_level.upper(), logging.INFO)

        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        channels = {
            'system': 'system.log',
            'download': 'download.log',
            'ocr': 'ocr.log',
            'error': 'error.log'
        }

        if gui_callback:
            cls._gui_handler = GUIHandler(gui_callback)
            cls._gui_handler.setFormatter(formatter)

        for channel, filename in channels.items():
            logger = logging.getLogger(f"dlrs.{channel}")
            logger.setLevel(level)
            logger.handlers.clear()

            file_handler = logging.FileHandler(os.path.join(log_dir, filename), encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            if cls._gui_handler:
                logger.addHandler(cls._gui_handler)

            cls._loggers[channel] = logger

        cls._initialized = True

    @classmethod
    def get_logger(cls, channel: str = 'system') -> logging.Logger:
        if not cls._initialized:
            cls.setup_loggers()
        return cls._loggers.get(channel, logging.getLogger("dlrs.system"))

def get_system_logger() -> logging.Logger:
    return LogManager.get_logger('system')

def get_download_logger() -> logging.Logger:
    return LogManager.get_logger('download')

def get_ocr_logger() -> logging.Logger:
    return LogManager.get_logger('ocr')

def get_error_logger() -> logging.Logger:
    return LogManager.get_logger('error')
