import os
from arlo_server import app

from config import FLASK_ENV, DEVELOPMENT_ENVS

if __name__ == "__main__":
    app.run(
        use_reloader=FLASK_ENV in DEVELOPMENT_ENVS,
        port=os.environ.get("PORT", 3001),
        host="0.0.0.0",
        threaded=True,
    )
