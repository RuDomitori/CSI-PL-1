import requests
import json
from tzlocal import get_localzone #pip install tzlocal

url = "http://localhost:8000/"
local_tz_name = get_localzone().__str__()

response = requests.get(url)
assert response.status_code == 200
assert local_tz_name in response.text

response = requests.get(url + "UTC")
assert response.status_code == 200
assert "UTC" in response.text

response = requests.get(url + "Europe/Moscow")
assert response.status_code == 200
assert "Europe/Moscow" in response.text

response = requests.get(url + "api")
assert response.status_code == 400

response = requests.get(url + "api/adss")
assert response.status_code == 404

response = requests.get(url + "api/adss")
assert response.status_code == 404

response = requests.get(url + "api/v1")
assert response.status_code == 404

response = requests.post(url + "api/v1/time")
assert response.status_code == 405

response = requests.get(url + "api/v1/time")
assert response.status_code == 200

response = requests.get(url + "api/v1/time")
assert response.status_code == 200
obj = json.loads(response.text)
assert obj["tz"] == local_tz_name

response = requests.get(url + "api/v1/time", params={"tz": "UTC"})
assert response.status_code == 200
obj = json.loads(response.text)
assert obj["tz"] == "UTC"

response = requests.get(url + "api/v1/time", params={"tz": "Europe/Moscow"})
assert response.status_code == 200
obj = json.loads(response.text)
assert obj["tz"] == "Europe/Moscow"

response = requests.get(url + "api/v1/time", params={"tz": "UFO"})
assert response.status_code == 404

response = requests.get(url + "api/v1/date", params={"tz": "Europe/Moscow"})
assert response.status_code == 200
obj = json.loads(response.text)
assert obj["tz"] == "Europe/Moscow"

response = requests.post(url + "api/v1/datediff", data= json.dumps({
    "start": {
        "date": "12:30pm 2020-12-01"
    },
    "end": {
        "date": "12.20.2021 22:21:05",
        "tz": "UTC"
    }
}))
assert response.status_code == 200
obj = json.loads(response.text)
assert obj["diff"]

response = requests.post(url + "api/v1/datediff", data= json.dumps({
    "begin": {
        "date": "12:30pm 2020-12-01",
        "timezone": local_tz_name
    },
    "end": {
        "date": "12.20.2021 22:21:05",
        "tz": "UTC"
    }
}))
assert response.status_code == 400
obj = json.loads(response.text)