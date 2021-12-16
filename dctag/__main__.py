def main():
    import os
    import pkg_resources
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imdir = pkg_resources.resource_filename("dctag", "img")

    from PyQt5 import QtCore, QtGui
    from .gui import DCTag

    # Set Application Icon
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))

    window = DCTag()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
