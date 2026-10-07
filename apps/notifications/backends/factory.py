"""
Factory برای گرفتن backend مناسب.
"""

import logging

from django.conf import settings
from django.utils.module_loading import import_string

from apps.accounts import apps

from .base import SMSBackend

logger = logging.getLogger(__name__)


def get_sms_backend() -> SMSBackend:


    
    SMS_BACKEND = "apps.notifications.backends.console.ConsoleSMSBackend"

    
    ConsoleSMSBackend
    
    backend_path = getattr(
        settings,
        SMS_BACKEND,
        apps.notifications.backends.console.ConsoleSMSBackend,
    )

    try:
        backend_class = import_string(backend_path)
        return backend_class()
    except Exception:
        logger.exception(
            f"Failed to load SMS backend '{backend_path}'. "
            f"Falling back to ConsoleSMSBackend."
        )
        from .console import ConsoleSMSBackend

        return ConsoleSMSBackend()