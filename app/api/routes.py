from flask import request
from app.api import bp, SIM


@bp.route('/', methods=['GET', 'POST'])
def api():
    if request.method == 'GET':
        return 'test api GET'

    data = request.get_json()

    con = SIM.number_pass(data.get('number'), data.get('pasword'), data.get('operator'))
    sim_data = con.get_data()

    return sim_data.__str__()
