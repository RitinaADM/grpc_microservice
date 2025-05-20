from src.domain.exceptions.base import BaseAppException

class DocumentNotFoundException(BaseAppException):
    def __str__(self):
        return "Document not found"

class InvalidInputException(BaseAppException):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message