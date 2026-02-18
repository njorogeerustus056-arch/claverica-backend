"""
cards/exceptions.py - Custom exceptions for cards app
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class CardException(APIException):
    """Base exception for card operations"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Card operation failed'
    default_code = 'card_error'


class InsufficientBalanceException(CardException):
    """Raised when insufficient balance for operation"""
    default_detail = 'Insufficient balance'
    default_code = 'insufficient_balance'


class CardNotFoundException(CardException):
    """Raised when card is not found"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Card not found'
    default_code = 'card_not_found'


class CardAlreadyExistsException(CardException):
    """Raised when card already exists"""
    default_detail = 'Card already exists'
    default_code = 'card_exists'


class CardLimitExceededException(CardException):
    """Raised when user exceeds card limit"""
    default_detail = 'Card limit exceeded'
    default_code = 'card_limit_exceeded'
