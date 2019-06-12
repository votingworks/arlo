import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='arlo-client/build/')

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + path):
        print(path)
        return send_from_directory(app.static_folder, path)
    else:
        print(path, "INDEX")
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(use_reloader=True, port=3001, threaded=True)
