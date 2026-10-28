"""The optional GUI package must not make PySide6 a base CLI import dependency."""


def test_gui_package_entrypoint_is_lazy():
    import sgokb.gui as gui

    assert callable(gui.main)
