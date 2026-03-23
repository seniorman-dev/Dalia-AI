# core/responses.py
from rest_framework.response import Response


class DaliaResponse:
    """
    Every API endpoint in Dalia returns this exact structure.
    My Flutter client will always knows what to expect.
    """

    @staticmethod
    def success(data=None, message="Success", status=200):
        return Response({
            "status": "success",
            "message": message,
            "data": data
        }, status=status)

    @staticmethod
    def error(message="Something went wrong", errors=None, status=400):
        return Response({
            "status": "error",
            "message": message,
            "errors": errors
        }, status=status)

    @staticmethod
    def unauthorized(message="Session expired. Please log in again."):
        return Response({
            "status": "error",
            "message": message,
            "errors": None
        }, status=401)