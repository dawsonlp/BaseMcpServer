"""Console output renders status icons, not enum member names."""

from io import StringIO

from rich.console import Console

from mcp_manager.cli.common.output import RichOutputManager, StatusIcon


def test_status_icon_formats_as_icon():
    assert f"{StatusIcon.SUCCESS}" == "✅"
    assert f"{StatusIcon.INFO}" == "ℹ️"


def test_messages_render_icons():
    buffer = StringIO()
    output = RichOutputManager(Console(file=buffer, no_color=True))
    output.success("done")
    output.info("note")
    text = buffer.getvalue()
    assert "StatusIcon" not in text
    assert "✅ done" in text
