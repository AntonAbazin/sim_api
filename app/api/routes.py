from flask import request
from app.api import bp, SIM


@bp.route('/', methods=['GET', 'POST'])
def api():
    if request.method == 'GET':
        return {'error': 'GET unsupported'}.__str__()

    try:
        data = request.get_json()
    except Exception as err:
        return {'error': str(err)}.__str__()

    number = data.get('number')
    password = data.get('password')
    operator = data.get('operator')

    error = []
    if not number:
        error.append('miss number')
    if not password:
        error.append('miss password')
    if not operator:
        error.append('miss operator')
    if len(error):
        return {'error': error}.__str__()

    con = SIM.number_pass(number, password, operator)
    data = con.get_data()

    return data.__str__()
