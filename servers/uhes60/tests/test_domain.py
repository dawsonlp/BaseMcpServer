import pytest
from domain.services import GreetingService
from domain.models import GreetingStyle

def test_greeting_service_creates_casual_greeting():
    service = GreetingService()
    result = service.create_greeting("Alice", GreetingStyle.CASUAL)
    
    assert result.success
    assert result.data.recipient == "Alice"
    assert result.data.style == GreetingStyle.CASUAL
    assert "Alice" in result.data.message

def test_greeting_service_validates_empty_name():
    service = GreetingService()
    result = service.create_greeting("", GreetingStyle.CASUAL)
    
    assert not result.success
    assert "empty" in result.error.message.lower()

def test_greeting_service_provides_templates():
    service = GreetingService()
    templates = service.get_available_templates()
    
    assert len(templates) == 3
    assert any(t.style == GreetingStyle.FORMAL for t in templates)
    assert any(t.style == GreetingStyle.CASUAL for t in templates)
    assert any(t.style == GreetingStyle.ENTHUSIASTIC for t in templates)
