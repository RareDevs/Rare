import sys

if __name__ == '__main__':
    if "--version" in sys.argv:
        from Rare import __version__

        print(__version__)
        exit(0)

    from Rare.Main import main
    main()

"""
    tray = QSystemTrayIcon()
    tray.setIcon(icon("fa.gamepad", color="white"))
    tray.setVisible(True)
    menu = QMenu()
    option1 = QAction("Geeks for Geeks")
    option1.triggered.connect(lambda: app.exec_())
    option2 = QAction("GFG")
    menu.addAction(option1)
    menu.addAction(option2)
    # To quit the app
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)
    # Adding options to the System Tray
    tray.setContextMenu(menu)"""
