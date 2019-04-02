import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser

headers = {'user-agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.99 YaBrowser/19.1.0.2644 Yowser/2.5 Safari/537.36',
           'Connection': 'keep-alive'}


def request_tele2(phone, password):
    resp_tele2 = {'balance': -1, 'trans': [], 'error': None}

    ses = requests.session()
    resp = ses.get(url='https://login.tele2.ru/ssotele2/wap/auth?serviceId=681&returnUrl=https://msk.tele2.ru/api/auth/sso/successLogin',
                   headers=headers)

    post_data = {'pNumber': phone,
                 'password': password,
                 'rememberMe': True,
                 'submit': 'Войти',
                 'formid': 'password-form'}

    soup = BeautifulSoup(resp.text, 'html.parser')
    tags = soup.find_all('input', type='hidden')
    for tag in tags:
        if tag.attrs.get('name') == '_csrf':
            post_data['_csrf'] = tag.attrs['value']
            break

    if not post_data.get('_csrf'):
        return {'balance': -1, 'trans': [], 'error': 'не найден csrf'}

    ses.post('https://login.tele2.ru/ssotele2/wap/auth/submitLoginAndPassword',
             headers=headers,
             data=post_data)

    url = 'https://msk.tele2.ru/api/subscribers/{}/'.format(phone)

    resp = ses.get(url + 'balance', headers=headers)
    try:
        resp_tele2['balance'] = json.loads(resp.text).get('data').get('value')
    except Exception as err:
        resp_tele2['error'] = 'Ошибка {}'.format(str(err))
        return resp_tele2

    date = datetime.today().date()
    params = '?fromDate={}T00%3A00%3A00%2B03%3A00&toDate={}T00%3A00%3A00%2B03%3A00'.\
        format(date - timedelta(days=10), date)

    resp = ses.get(url + 'payments' + params, headers=headers)
    try:
        data = json.loads(resp.text).get('data')
        for tr in data:
            resp_tele2['trans'].append({'data': parser.parse(tr.get('payDate')),
                                        'sum': tr.get('sum').get('amount'),
                                        'desc': tr.get('type')})
    except Exception as err:
        resp_tele2['error'] = 'Ошибка {}'.format(str(err))
        return resp_tele2

    return resp_tele2


def mts_redirect(ses, html):

    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all('body')
    onload = tags[0].attrs.get('onload')
    if not onload:
        return

    tags = soup.find_all('form')
    action = tags[0].attrs.get('action')

    post_data = {}

    tags = soup.find_all('input', type='hidden')
    for tag in tags:
        if tag.attrs.get('name') == 'csrf.sign':
            post_data['csrf.sign'] = tag.attrs.get('value')
            break

    headers['Origin'] = 'http://login.mts.ru'
    headers['Referer'] = 'http://login.mts.ru/amserver/UI/Login?service=lk&goto=https%3a%2f%2flk.ssl.mts.ru%2f'

    resp = ses.post(action, headers=headers, data=post_data)

    soup = BeautifulSoup(resp.text, 'html.parser')
    tags = soup.find_all('form')
    action = tags[0].attrs.get('action')

    tags = soup.find_all('input', type='hidden')
    for tag in tags:
        name = tag.attrs.get('name')
        if name == 'csrf.sign':     post_data['csrf.sign'] = tag.attrs.get('value')
        if name == 'csrf.ts':       post_data['csrf.ts'] = tag.attrs.get('value')

    resp = ses.post(action, headers=headers, data=post_data)

    return resp.text


def mts_auth(ses, phone, password):

    resp = ses.get('https://lk.ssl.mts.ru/', headers=headers)
    html = resp.text

    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all('meta')
    for tag in tags:
        if tag.attrs.get('name') == 'lkMonitorCheck':
            return True

    html = mts_redirect(ses, html)

    headers['Origin'] = 'https://login.mts.ru'
    headers['Referer'] = 'https://login.mts.ru/amserver/UI/Login?service=lk&goto=https%3a%2f%2flk.ssl.mts.ru%2f'

    post_data = {'rememberme': 'on',
                 'IDButton': 'Submit',
                 'encoded': False,
                 'IDToken1': phone[1:len(phone)],
                 'IDToken2': password}

    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all('input')
    for tag in tags:
        name = tag.attrs.get('name')
        if name == 'loginURL':      post_data['loginURL'] = tag.attrs.get('value')
        elif name == 'csrf.sign':   post_data['csrf.sign'] = tag.attrs.get('value')
        elif name == 'csrf.ts':     post_data['csrf.ts'] = tag.attrs.get('value')

    ses.post('https://login.mts.ru/amserver/UI/Login?service=lk&goto=http%3a%2f%2flk.ssl.mts.ru%2f',
             headers=headers,
             data=post_data)

    return


def request_mts(phone, password):
    resp_mts = {'balance': -1, 'trans': [], 'error': None}

    ses = requests.session()

    mts_auth(ses, phone, password)

    str_data1 = '{:%d.%m.%Y}'.format(datetime.today().date() - timedelta(days=10))
    str_data2 = '{:%d.%m.%Y}'.format(datetime.today().date())

    post_data = {'ctl00_sm_HiddenField': '',
                 'csrfToken': '',
                 '__EVENTTARGET': '',
                 '__EVENTARGUMENT': '',
                 '__VIEWSTATE': '',
                 '__VIEWSTATEGENERATOR': '',
                 '__EVENTVALIDATION': '',
                 'ctl00$MainContent$ActiveTabName': 'paymentHistory',
                 'ctl00$MainContent$drp$from': str_data1,
                 'ctl00$MainContent$drp$to': str_data2,
                 'ctl00$MainContent$searchButton': 'OK'
                 }

    resp = ses.get('https://ihelper.mts.ru/selfcare/payment-full-history.aspx')
    soup = BeautifulSoup(resp.text, 'html.parser')
    inputs = soup.find_all('input')
    for input in inputs:
        name = input.attrs['name']
        if not post_data[name]:
            post_data[name] = input.attrs['value']

    resp = ses.post('https://ihelper.mts.ru/selfcare/payment-full-history.aspx',
             headers=headers,
             data=post_data)
    soup = BeautifulSoup(resp.text, 'html.parser')
    divs = soup.find_all('div')
    for div in divs:
        div_id = div.attrs.get('id')
        if div_id == 'ctl00_MainContent_paymentsGridium_div':
            table = div.contents[1].contents[2]
            for row in table:
                if row == '\n':
                    continue
                resp_mts['trans'].append({'data': parser.parse(row.contents[1].text),
                                          'sum': float(row.contents[3].text.replace(',', '.').replace(' ', '')),
                                          'desc': row.contents[2].text})
            break


    resp = ses.get('https://login.mts.ru/profile/header?ref=https%3A//ihelper.mts.ru/selfcare/payment-full-history.aspx&scheme=https&style=2015v2&updat')
    soup = BeautifulSoup(resp.text, 'html.parser')
    spans = soup.find_all('span')
    for span in spans:
        try:
            cur = span.contents[1]
        except:
            continue
        if 'руб' in cur:
            resp_mts['balance'] = float(span.contents[0].contents[0])
            break

    return resp_mts


def request_megafon(phone, password):
    resp_meg = {'balance': -1, 'trans': [], 'error': None}

    CSRF = None

    ses = requests.session()
    resp = ses.get('https://lk.megafon.ru/login/', headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    inputs = soup.find_all('input', type='hidden')
    for input in inputs:
        if input.attrs.get('name') == 'CSRF':
            CSRF = input.attrs.get('value')
            break

    if not CSRF:
        resp_meg['error'] = 'Ошибка CSRF'
        return resp_meg

    post_data = {'j_username': phone,
                 'j_password': password,
                 'CSRF': CSRF}

    resp = ses.post('https://lk.megafon.ru/dologin/', headers=headers, data=post_data)
    if not resp.status_code == 200:
        resp_meg['error'] = 'Ошибка логина'
        return resp_meg

    resp = ses.get('https://lk.megafon.ru/api/payments/history/?size=30')
    if resp.status_code == 200:
        payments = json.loads(resp.text).get('payments')
        for paymet in payments:
            resp_meg['trans'].append({'data': paymet.get('date'),
                                      'sum': paymet.get('amount'),
                                      'desc': paymet.get('descr')})

    resp = ses.get('https://lk.megafon.ru/api/lk/balance/get?')
    if resp.status_code == 200:
        resp_meg['balance'] = json.loads(resp.text).get('balance')

    return resp_meg


def number_pass(number, password, operator):
    conn = Connection()
    conn._set_phone(number, password, operator)
    return conn


class Connection():
    def __init__(self):
        self.number = None
        self.password = None
        self.operator = None

    def _set_phone(self, number, password, operator):
        self.number = number
        self.password = password
        self.operator = operator

    def get_data(self):
        if self.operator == 'tele2':
            return request_tele2(self.number, self.password)
        elif self.operator == 'mts':
            return request_mts(self.number, self.password)
        elif self.operator == 'megafon':
            return request_megafon(self.number, self.password)
        return {'error': 'unsupported operator ' + self.operator}
