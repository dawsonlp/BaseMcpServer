"""Pydantic v2 model-validation regressions."""

import pytest
from pydantic import ValidationError

from mcp_manager.core.models import Server, ServerType


def test_server_name_uses_functional_validation():
    server = Server(name="valid-name_2", server_type=ServerType.LOCAL)
    assert server.name == "valid-name_2"

    with pytest.raises(ValidationError, match="alphanumeric"):
        Server(name="invalid name", server_type=ServerType.LOCAL)
