"""Optional PySide6 desktop client for SGOKB."""


def main() -> int:
    """Load the Qt GUI lazily so base CLI installs do not require PySide6."""

    from .main import main as gui_main

    return gui_main()


__all__ = ["main"]
