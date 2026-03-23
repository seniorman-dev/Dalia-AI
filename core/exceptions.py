# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from core.responses import DaliaResponse


def custom_exception_handler(exc, context):
    if isinstance(exc, Throttled):
        wait = exc.wait
        seconds = int(wait) if wait else 'a few'
        return DaliaResponse.error(
            message=f"Too many requests. Please wait {seconds} seconds before trying again.",
            status=429
        )
    
    return exception_handler(exc, context)