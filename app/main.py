import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.session import init_db
from ui.app import App


def main():
    init_db()
    app = App()
    app.run()


if __name__ == "__main__":
    main()