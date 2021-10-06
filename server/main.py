import os
from .config import FLASK_ENV
from .app import app

if __name__ == "__main__":
    app.run(
        use_reloader=FLASK_ENV in ["development", "test"],
        port=os.environ.get("PORT", 3001),
        host="0.0.0.0",
        threaded=True,
    )
