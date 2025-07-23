"""
Safe enums for fixed Jira values.

This module contains enums only for values that are fixed in Jira and cannot
be customized by administrators. Configurable values use flexible value objects instead.
"""

from enum import Enum


class StatusCategory(Enum):
    """
    Enumeration of Jira status categories.
    
    These three categories are fixed in Jira and cannot be customized.
    All custom statuses must map to one of these categories.
    """
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    
    def __str__(self) -> str:
        """String representation of the status category."""
        return self.value
    
    @classmethod
    def from_string(cls, category_str: str) -> "StatusCategory":
        """Create StatusCategory from string with case-insensitive matching."""
        category_map = {
            "to do": cls.TODO,
            "todo": cls.TODO,
            "in progress": cls.IN_PROGRESS,
            "inprogress": cls.IN_PROGRESS,
            "done": cls.DONE,
            "complete": cls.DONE,
            "completed": cls.DONE,
        }
        
        normalized = category_str.lower().strip()
        if normalized in category_map:
            return category_map[normalized]
        
        # Try exact match with original values
        for category in cls:
            if category.value.lower() == normalized:
                return category
        
        raise ValueError(f"Unknown status category: '{category_str}'. Valid categories: To Do, In Progress, Done")


class LinkDirection(Enum):
    """
    Enumeration of link directions.
    
    These directions are fixed in Jira's link system and cannot be customized.
    """
    INWARD = "inward"
    OUTWARD = "outward"
    
    def __str__(self) -> str:
        """String representation of the link direction."""
        return self.value
    
    @classmethod
    def from_string(cls, direction_str: str) -> "LinkDirection":
        """Create LinkDirection from string with case-insensitive matching."""
        normalized = direction_str.lower().strip()
        
        if normalized == "inward":
            return cls.INWARD
        elif normalized == "outward":
            return cls.OUTWARD
        else:
            raise ValueError(f"Unknown link direction: '{direction_str}'. Valid directions: inward, outward")
    
    def reverse(self) -> "LinkDirection":
        """Get the opposite direction."""
        return LinkDirection.INWARD if self == LinkDirection.OUTWARD else LinkDirection.OUTWARD


class TimeUnit(Enum):
    """
    Enumeration of time units for work logging.
    
    These time units are standardized in Jira and cannot be customized.
    """
    MINUTES = "m"
    HOURS = "h"
    DAYS = "d"
    WEEKS = "w"
    
    def __str__(self) -> str:
        """String representation of the time unit."""
        return self.value
    
    @property
    def seconds(self) -> int:
        """Get the number of seconds in this time unit."""
        unit_seconds = {
            TimeUnit.MINUTES: 60,
            TimeUnit.HOURS: 3600,
            TimeUnit.DAYS: 28800,    # 8-hour work day
            TimeUnit.WEEKS: 144000,  # 5-day work week (5 * 8 hours)
        }
        return unit_seconds[self]
    
    @property
    def full_name(self) -> str:
        """Get the full name of the time unit."""
        unit_names = {
            TimeUnit.MINUTES: "minutes",
            TimeUnit.HOURS: "hours",
            TimeUnit.DAYS: "days",
            TimeUnit.WEEKS: "weeks",
        }
        return unit_names[self]
    
    @classmethod
    def from_string(cls, unit_str: str) -> "TimeUnit":
        """Create TimeUnit from string with flexible matching."""
        normalized = unit_str.lower().strip()
        
        # Direct matches
        unit_map = {
            "m": cls.MINUTES,
            "min": cls.MINUTES,
            "mins": cls.MINUTES,
            "minute": cls.MINUTES,
            "minutes": cls.MINUTES,
            "h": cls.HOURS,
            "hr": cls.HOURS,
            "hrs": cls.HOURS,
            "hour": cls.HOURS,
            "hours": cls.HOURS,
            "d": cls.DAYS,
            "day": cls.DAYS,
            "days": cls.DAYS,
            "w": cls.WEEKS,
            "wk": cls.WEEKS,
            "week": cls.WEEKS,
            "weeks": cls.WEEKS,
        }
        
        if normalized in unit_map:
            return unit_map[normalized]
        
        raise ValueError(f"Unknown time unit: '{unit_str}'. Valid units: m, h, d, w")
    
    def convert_to_seconds(self, amount: int) -> int:
        """Convert an amount of this unit to seconds."""
        return amount * self.seconds
    
    def convert_from_seconds(self, seconds: int) -> int:
        """Convert seconds to this unit (rounded down)."""
        return seconds // self.seconds


class WorkLogAdjustment(Enum):
    """
    Enumeration of work log estimate adjustment options.
    
    These adjustment types are fixed in Jira's time tracking system.
    """
    AUTO = "auto"           # Automatically reduce remaining estimate
    NEW = "new"             # Set new remaining estimate
    LEAVE = "leave"         # Leave remaining estimate unchanged
    MANUAL = "manual"       # Manually reduce remaining estimate by specified amount
    
    def __str__(self) -> str:
        """String representation of the adjustment type."""
        return self.value
    
    @classmethod
    def from_string(cls, adjustment_str: str) -> "WorkLogAdjustment":
        """Create WorkLogAdjustment from string with case-insensitive matching."""
        normalized = adjustment_str.lower().strip()
        
        for adjustment in cls:
            if adjustment.value == normalized:
                return adjustment
        
        raise ValueError(f"Unknown work log adjustment: '{adjustment_str}'. Valid adjustments: auto, new, leave, manual")
    
    def requires_new_estimate(self) -> bool:
        """Check if this adjustment type requires a new estimate value."""
        return self in {WorkLogAdjustment.NEW, WorkLogAdjustment.MANUAL}
    
    def requires_reduce_by(self) -> bool:
        """Check if this adjustment type requires a reduce-by value."""
        return self == WorkLogAdjustment.MANUAL
