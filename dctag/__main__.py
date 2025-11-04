def main():
    import importlib.resources
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    from PyQt6 import QtCore, QtGui
    from .gui import DCTag

    # Set Application Icon
    ref = importlib.resources.files("dctag.img") / "icon.png"
    with importlib.resources.as_file(ref) as icon_path:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))

    window = DCTag()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
