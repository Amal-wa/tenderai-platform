# ==============================================================================
# scheduler/logger.py - Configuration du logging
# ==============================================================================

import logging
import sys
from logging import StreamHandler
from pythonjsonlogger import jsonlogger
from config import settings


def setup_logging():
    """Configure le logging avec format JSON pour les logs."""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Handler avec JSON formatter
    handler = StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    return root_logger


logger = setup_logging()
