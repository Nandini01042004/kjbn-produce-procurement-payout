"""
Domain Exception Types for Produce Procurement & Payout
Distinct error types mapped cleanly to HTTP status codes with structured messages.
"""

from typing import Optional


class DomainError(Exception):
    """Base class for all business rule and domain errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class MissingPriceListError(DomainError):
    def __init__(self, crop_name: str, grade: str, delivered_on: str):
        message = (
            f"No active price-list entry found for crop '{crop_name}' and grade '{grade}' "
            f"on or before {delivered_on}."
        )
        super().__init__(message=message, code="PRICE_LIST_NOT_FOUND", status_code=400)


class MoistureExceededError(DomainError):
    def __init__(self, moisture: str, max_accepted: str, crop_name: str):
        message = (
            f"Delivery moisture of {moisture}% exceeds maximum accepted moisture "
            f"of {max_accepted}% for {crop_name}. Produce rejected."
        )
        super().__init__(message=message, code="MAX_MOISTURE_EXCEEDED", status_code=422)


class InvalidGradeError(DomainError):
    def __init__(self, grade: str, crop_name: str, allowed_grades: list[str]):
        message = (
            f"Invalid grade '{grade}' for crop '{crop_name}'. "
            f"Allowed grades are: {', '.join(allowed_grades)}."
        )
        super().__init__(message=message, code="INVALID_GRADE", status_code=422)


class NegativeValueError(DomainError):
    def __init__(self, field_name: str, value: str):
        message = f"Field '{field_name}' must be strictly positive (> 0), got {value}."
        super().__init__(message=message, code="VALUE_MUST_BE_POSITIVE", status_code=422)


class FutureDateError(DomainError):
    def __init__(self, delivered_on: str, current_time: str):
        message = f"Delivery date '{delivered_on}' is in the future (current system time: '{current_time}')."
        super().__init__(message=message, code="FUTURE_DATE_REJECTED", status_code=422)


class ImmutablePayoutError(DomainError):
    def __init__(self, message: str = "A finalised payout is immutable and cannot be modified or deleted."):
        super().__init__(message=message, code="PAYOUT_IMMUTABLE", status_code=409)


class ImmutableDeliveryError(DomainError):
    def __init__(self, delivery_id: int, payout_id: int):
        message = (
            f"Delivery #{delivery_id} belongs to Finalised Payout #{payout_id} and cannot be modified. "
            f"Submit a credit/debit note delivery to make corrections."
        )
        super().__init__(message=message, code="DELIVERY_IMMUTABLE", status_code=409)


class EntityNotFoundError(DomainError):
    def __init__(self, entity_name: str, entity_id: int):
        message = f"{entity_name} with ID {entity_id} was not found."
        super().__init__(message=message, code="ENTITY_NOT_FOUND", status_code=404)
