import os
from arlo_server import app

if __name__ == '__main__':
    app.run(use_reloader=True, port=os.environ.get('PORT', 3001), host='0.0.0.0', threaded=True)
