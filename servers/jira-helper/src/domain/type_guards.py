"""
Type guards and validation utilities for domain value objects.

This module provides runtime type checking and validation functions
for value objects and domain types, enhancing type safety.
"""

import re
from typing import Any, TypeGuard

from domain.value_objects import (
    IssueKey, ProjectKey, TimeSpan, JqlQuery, InstanceName,
)
from domain.enums import StatusCategory, LinkDirection, TimeUnit, WorkLogAdjustment

from domain.shared_data import UserInfo, TimeTracking, IssueMetadata


def is_issue_key(value: Any) -> TypeGuard[IssueKey]:
    """Type guard to check if a value is a valid IssueKey."""
    if not isinstance(value, IssueKey):
        return False
    
    try:
        # Validate the pattern
        pattern = re.compile(r'^[A-Z][A-Z0-9]*-\d+$')
        return bool(pattern.match(value.value))
    except (AttributeError, TypeError):
        return False


def is_project_key(value: Any) -> TypeGuard[ProjectKey]:
    """Type guard to check if a value is a valid ProjectKey."""
    if not isinstance(value, ProjectKey):
        return False
    
    try:
        # Validate the pattern
        pattern = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')
        return bool(pattern.match(value.value))
    except (AttributeError, TypeError):
        return False


def is_time_span(value: Any) -> TypeGuard[TimeSpan]:
    """Type guard to check if a value is a valid TimeSpan."""
    if not isinstance(value, TimeSpan):
        return False
    
    try:
        return value.total_seconds >= 0
    except (AttributeError, TypeError):
        return False


def is_jql_query(value: Any) -> TypeGuard[JqlQuery]:
    """Type guard to check if a value is a valid JqlQuery."""
    if not isinstance(value, JqlQuery):
        return False
    
    try:
        return bool(value.query and value.query.strip())
    except (AttributeError, TypeError):
        return False


def is_instance_name(value: Any) -> TypeGuard[InstanceName]:
    """Type guard to check if a value is a valid InstanceName."""
    if not isinstance(value, InstanceName):
        return False
    
    try:
        pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
        return bool(pattern.match(value.name))
    except (AttributeError, TypeError):
        return False


def is_status_category(value: Any) -> TypeGuard[StatusCategory]:
    """Type guard to check if a value is a valid StatusCategory."""
    return isinstance(value, StatusCategory)


def is_link_direction(value: Any) -> TypeGuard[LinkDirection]:
    """Type guard to check if a value is a valid LinkDirection."""
    return isinstance(value, LinkDirection)


def is_time_unit(value: Any) -> TypeGuard[TimeUnit]:
    """Type guard to check if a value is a valid TimeUnit."""
    return isinstance(value, TimeUnit)


def is_work_log_adjustment(value: Any) -> TypeGuard[WorkLogAdjustment]:
    """Type guard to check if a value is a valid WorkLogAdjustment."""
    return isinstance(value, WorkLogAdjustment)


def is_user_info(value: Any) -> TypeGuard[UserInfo]:
    """Type guard to check if a value is a valid UserInfo."""
    if not isinstance(value, UserInfo):
        return False
    
    try:
        # UserInfo is valid if it has at least one identifier
        return value.is_valid()
    except (AttributeError, TypeError):
        return False


def is_time_tracking(value: Any) -> TypeGuard[TimeTracking]:
    """Type guard to check if a value is a valid TimeTracking."""
    if not isinstance(value, TimeTracking):
        return False
    
    try:
        # Check that any TimeSpan values are valid
        for time_value in [value.original_estimate, value.remaining_estimate, value.time_spent]:
            if time_value is not None and not is_time_span(time_value):
                return False
        return True
    except (AttributeError, TypeError):
        return False


def is_issue_metadata(value: Any) -> TypeGuard[IssueMetadata]:
    """Type guard to check if a value is a valid IssueMetadata."""
    return isinstance(value, IssueMetadata)


# Validation functions for string inputs
def validate_issue_key_string(key_str: str) -> bool:
    """Validate if a string can be converted to a valid IssueKey."""
    if not isinstance(key_str, str) or not key_str.strip():
        return False
    
    pattern = re.compile(r'^[A-Z][A-Z0-9]*-\d+$')
    return bool(pattern.match(key_str.strip().upper()))


def validate_project_key_string(key_str: str) -> bool:
    """Validate if a string can be converted to a valid ProjectKey."""
    if not isinstance(key_str, str) or not key_str.strip():
        return False
    
    pattern = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')
    return bool(pattern.match(key_str.strip().upper()))


def validate_time_span_string(time_str: str) -> bool:
    """Validate if a string can be converted to a valid TimeSpan."""
    if not isinstance(time_str, str) or not time_str.strip():
        return False
    
    # Pattern to match time components: number + unit
    pattern = re.compile(r'(\d+)([wdhm])')
    matches = pattern.findall(time_str.lower().strip())
    
    if not matches:
        return False
    
    # Check that all units are valid
    valid_units = {'w', 'd', 'h', 'm'}
    for _, unit in matches:
        if unit not in valid_units:
            return False
    
    return True


def validate_instance_name_string(name_str: str) -> bool:
    """Validate if a string can be converted to a valid InstanceName."""
    if not isinstance(name_str, str) or not name_str.strip():
        return False
    
    pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    return bool(pattern.match(name_str.strip().lower()))


def validate_jql_string(jql_str: str) -> bool:
    """Validate if a string can be converted to a valid JqlQuery."""
    if not isinstance(jql_str, str) or not jql_str.strip():
        return False
    
    # Check for potentially dangerous patterns
    dangerous_patterns = ['drop', 'delete', 'insert', 'update', 'create', 'alter']
    query_lower = jql_str.lower()
    
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            return False
    
    return True


# Safe conversion functions that return None on failure
def safe_issue_key(value: Any) -> IssueKey | None:
    """Safely convert a value to IssueKey, returning None on failure."""
    try:
        if isinstance(value, IssueKey):
            return value if is_issue_key(value) else None
        elif isinstance(value, str):
            return IssueKey.from_string(value) if validate_issue_key_string(value) else None
        else:
            return None
    except (ValueError, TypeError):
        return None


def safe_project_key(value: Any) -> ProjectKey | None:
    """Safely convert a value to ProjectKey, returning None on failure."""
    try:
        if isinstance(value, ProjectKey):
            return value if is_project_key(value) else None
        elif isinstance(value, str):
            return ProjectKey.from_string(value) if validate_project_key_string(value) else None
        else:
            return None
    except (ValueError, TypeError):
        return None


def safe_time_span(value: Any) -> TimeSpan | None:
    """Safely convert a value to TimeSpan, returning None on failure."""
    try:
        if isinstance(value, TimeSpan):
            return value if is_time_span(value) else None
        elif isinstance(value, str):
            return TimeSpan.from_string(value) if validate_time_span_string(value) else None
        elif isinstance(value, int) and value >= 0:
            return TimeSpan(value)
        else:
            return None
    except (ValueError, TypeError):
        return None


def safe_jql_query(value: Any) -> JqlQuery | None:
    """Safely convert a value to JqlQuery, returning None on failure."""
    try:
        if isinstance(value, JqlQuery):
            return value if is_jql_query(value) else None
        elif isinstance(value, str):
            return JqlQuery.from_string(value) if validate_jql_string(value) else None
        else:
            return None
    except (ValueError, TypeError):
        return None


def safe_instance_name(value: Any) -> InstanceName | None:
    """Safely convert a value to InstanceName, returning None on failure."""
    try:
        if isinstance(value, InstanceName):
            return value if is_instance_name(value) else None
        elif isinstance(value, str):
            return InstanceName.from_string(value) if validate_instance_name_string(value) else None
        else:
            return None
    except (ValueError, TypeError):
        return None


# Batch validation functions
def validate_issue_keys(keys: list[str]) -> tuple[list[IssueKey], list[str]]:
    """
    Validate a list of issue key strings.
    
    Returns:
        Tuple of (valid_keys, invalid_keys)
    """
    valid_keys = []
    invalid_keys = []
    
    for key_str in keys:
        issue_key = safe_issue_key(key_str)
        if issue_key:
            valid_keys.append(issue_key)
        else:
            invalid_keys.append(key_str)
    
    return valid_keys, invalid_keys


def validate_project_keys(keys: list[str]) -> tuple[list[ProjectKey], list[str]]:
    """
    Validate a list of project key strings.
    
    Returns:
        Tuple of (valid_keys, invalid_keys)
    """
    valid_keys = []
    invalid_keys = []
    
    for key_str in keys:
        project_key = safe_project_key(key_str)
        if project_key:
            valid_keys.append(project_key)
        else:
            invalid_keys.append(key_str)
    
    return valid_keys, invalid_keys


def validate_time_spans(time_strings: list[str]) -> tuple[list[TimeSpan], list[str]]:
    """
    Validate a list of time span strings.
    
    Returns:
        Tuple of (valid_time_spans, invalid_time_strings)
    """
    valid_spans = []
    invalid_strings = []
    
    for time_str in time_strings:
        time_span = safe_time_span(time_str)
        if time_span:
            valid_spans.append(time_span)
        else:
            invalid_strings.append(time_str)
    
    return valid_spans, invalid_strings
