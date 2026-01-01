# payments/exceptions.py
"""
Custom exceptions for payments app
"""


class PaymentException(Exception):
    """Base payment exception"""
    pass


class InsufficientFundsException(PaymentException):
    """Raised when account has insufficient funds"""
    pass


class InvalidCurrencyException(PaymentException):
    """Raised when currency is invalid or unsupported"""
    pass


class PaymentGatewayException(PaymentException):
    """Raised when payment gateway fails"""
    pass


class TransactionNotFoundException(PaymentException):
    """Raised when transaction is not found"""
    pass


class DuplicateTransactionException(PaymentException):
    """Raised when duplicate transaction is detected"""
    pass


class CardSecurityException(PaymentException):
    """Raised for card security violations"""
    pass