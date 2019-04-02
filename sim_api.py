from app import create_app

app = create_app()


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return 'ok'


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)
