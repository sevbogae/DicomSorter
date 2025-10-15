from dicomsorter.userinterface.mainview import MainView


def main() -> None:
    """Main entry point for the dicomsorter application."""
    app = MainView()
    app.run()


if __name__ == "__main__":
    main()
