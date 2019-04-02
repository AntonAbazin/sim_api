from flask import send_from_directory
from app import create_app
import os

app = create_app()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.png',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return 'ok'


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)
