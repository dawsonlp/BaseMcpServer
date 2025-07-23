"""
Universal input validator for application layer.

Minimal validation - let Jira be the authoritative validator for business rules.
Only validate obviously malformed input (null/empty values).
"""

from domain.exceptions import JiraValidationError


def validate(**kwargs):
    """
    Universal input validator for application layer.
    
    Usage:
        validate(
            issue_key=issue_key,
            time_spent=time_spent,
            required=['issue_key', 'time_spent'],
            positive=['max_results'],
            non_negative=['start_at']
        )
    
    Args:
        **kwargs: Field values and validation rules
        
    Validation Rules:
        required: List of field names that cannot be empty
        positive: List of field names that must be > 0
        non_negative: List of field names that must be >= 0
        at_least_one: List of field names where at least one must be provided
        
    Raises:
        JiraValidationError: If validation fails
    """
    # Extract validation rules
    required = kwargs.pop('required', [])
    positive = kwargs.pop('positive', [])
    non_negative = kwargs.pop('non_negative', [])
    at_least_one = kwargs.pop('at_least_one', [])
    
    errors = []
    
    # Required field validation
    for field_name in required:
        if field_name not in kwargs or not _is_valid_value(kwargs[field_name]):
            errors.append(f"{_humanize(field_name)} cannot be empty")
    
    # Positive number validation
    for field_name in positive:
        if field_name in kwargs and kwargs[field_name] <= 0:
            errors.append(f"{_humanize(field_name)} must be greater than 0")
    
    # Non-negative number validation
    for field_name in non_negative:
        if field_name in kwargs and kwargs[field_name] < 0:
            errors.append(f"{_humanize(field_name)} cannot be negative")
    
    # At least one field validation
    if at_least_one:
        if not any(kwargs.get(field_name) for field_name in at_least_one):
            field_names = ', '.join(_humanize(name) for name in at_least_one)
            errors.append(f"At least one of the following must be provided: {field_names}")
    
    if errors:
        raise JiraValidationError(errors)


def _is_valid_value(value) -> bool:
    """Check if a value is valid (not None, not empty string)."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, dict) and not value:
        return False
    return True


def _humanize(field_name: str) -> str:
    """Convert snake_case field name to human readable format."""
    return field_name.replace('_', ' ').title()
