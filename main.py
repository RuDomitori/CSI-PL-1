from wsgiref.simple_server import make_server
from wsgiref import util
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

import pytz #pip install pytz
from tzlocal import get_localzone #pip install tzlocal

import json

def time_app(environ, start_response):
    req = request(environ)
    if req.path_parts[0] == 'api':
        return api(req, start_response)
    else:
        return index(req, start_response)

def index(req, start_response):
    tz_name = '/'.join(req.path_parts[0:])
    timestamp = get_timestamp_by_tz_name(tz_name)
    if not timestamp:
        start_response(
            status = '404 NOT FOUND',
            headers = [('Content-type', 'text/html; charset=utf-8')]
        )
        return error_html.format(
            message = f"Timezone '{tz_name}' does not exist"
        ).encode().splitlines()
    else:
        start_response(
            status = '200 OK',
            headers = [('Content-type', 'text/html; charset=utf-8')]
        )
        return index_html.format(
            time = timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            tz = timestamp.tzinfo.__str__()
        ).encode().splitlines()

def api(req, start_response):
    if len(req.path_parts) < 2:
        start_response(
            status = '400 BAD REQUEST',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        return json.dumps({
            "status": 400,
            "message": "API version not specified",
            "existed versions": [*(api_versions.keys())]
        }).encode().splitlines()
    elif req.path_parts[1] not in api_versions:
        start_response(
            status = '404 NOT FOUND',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        return json.dumps({
            "status": 404,
            "message": "API version not found",
            "existed versions": [*(api_versions.keys())]
        }).encode().splitlines()
    else:
        return api_versions[req.path_parts[1]](req, start_response)

class request:
    def __init__(self, environ):
        self.method = environ.get("REQUEST_METHOD")
        parse_res = urlparse(util.request_uri(environ))
        self.scheme = parse_res.scheme
        self.netloc = parse_res.netloc
        self.path_parts = parse_res.path.split('/')[1:]
        self.params = parse_qs(parse_res.query)
        try:
            count = int(environ.get("CONTENT_LENGTH", "0"))
        except:
            count = 0
        self.body = environ["wsgi.input"].read(count)

def api_v1(req, start_response):
    api_name = '/'.join(req.path_parts[2:])
    if api_name not in v1_apis:
        start_response(
            status = '404 NOT FOUND',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        return json.dumps({
            "status": 404,
            "message": "API not found",
            "existed APIs": [*v1_apis.keys()]
        }).encode().splitlines()
    
    if req.method not in v1_apis[api_name]:
        start_response(
            status = '405 METHOD NOT ALLOW',
            headers = [
                ('Content-type', 'application/json; charset=utf-8'),
                ("Allow", ", ".join(v1_apis[api_name].keys()))
            ]
        )
        return json.dumps({
            "status": 405,
            "message": f"Method '{req.method}' not allowed for API '{api_name}'",
            "allowed methods": [*v1_apis[api_name].keys()]
        }).encode().splitlines()
    else: 
        return v1_apis[api_name][req.method](req, start_response)

def datetime_api_v1(req, start_response):
    tz_name = req.params.get("tz")
    tz_name = tz_name[0] if tz_name else None
    timestamp = get_timestamp_by_tz_name(tz_name)
    if not timestamp:
        start_response(
            status = '404 NOT FOUND',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        return json.dumps({
            "status": 404,
            "message": f"Timezone {tz_name} does not exist",
        }).encode().splitlines()
    else:
        start_response(
            status = '200 OK',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        obj = {"tz": timestamp.tzinfo.__str__()}
        if req.path_parts[2] == "time":
            obj["time"] = timestamp.strftime('%H:%M:%S')
        else:
            obj["date"] = timestamp.strftime('%Y-%m-%d')
        return json.dumps(obj).encode().splitlines()

def get_timestamp_by_tz_name(tz_name):
    if not tz_name:
        return datetime.now(tz=get_localzone())
    elif tz_name not in pytz.all_timezones:
        return None
    else:
        return datetime.now(tz=pytz.timezone(tz_name))

def datediff_api_v1(req, start_response):
    try:
        body = json.loads(req.body)
        try: 
            timestamp1 = datetime.strptime(body["start"]["date"], '%m.%d.%Y %H:%M:%S')
        except:
            timestamp1 = datetime.strptime(body["start"]["date"], '%H:%M%p %Y-%m-%d')
        tz1 = get_localzone() if "tz" not in body["start"] else pytz.timezone(body["start"]["tz"])
        timestamp1 = tz1.localize(timestamp1)
        
        try:
            timestamp2 = datetime.strptime(body["end"]["date"], '%m.%d.%Y %H:%M:%S')
        except:
            timestamp2 = datetime.strptime(body["end"]["date"], '%H:%M%p %Y-%m-%d')
        tz2 = get_localzone() if "tz" not in body["end"] else pytz.timezone(body["end"]["tz"])
        timestamp2 = tz2.localize(timestamp2)
    except:
        start_response(
            status = '400 BAD REQUEST',
            headers = [('Content-type', 'application/json; charset=utf-8')]
        )
        return json.dumps({
            "status": 400,
            "message": "Bad json",
        }).encode().splitlines()

    diff = timestamp2 - timestamp1
    start_response(
        status = '200 OK',
        headers = [('Content-type', 'application/json; charset=utf-8')]
    )
    return json.dumps({
        "diff": diff.__str__()
    }).encode().splitlines()

api_versions = {
    "v1": api_v1
}

v1_apis = {
    "time": {
        "GET": datetime_api_v1
    },
    "date": {
        "GET": datetime_api_v1
    },
    "datediff": {
        "POST": datediff_api_v1
    } 
}

index_html = ""
for line in open('index.html', "r").readlines():
    index_html += line

error_html = ""
for line in open('error.html', "r").readlines():
    error_html += line

with make_server('', 8000, time_app) as httpd:
    print("Serving on port 8000...")

    # Serve until process is killed
    httpd.serve_forever()