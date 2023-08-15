import json
import elasticapm
from elasticapm.contrib.flask import ElasticAPM
from flask import Flask, request, jsonify
# Initialize flask app for the example
app = Flask(__name__)

app.config["ELASTIC_APM"] = {
    "SERVICE_NAME": "apm_system",
    "SECRET_TOKEN": "7WEBpjcgRNleDWX4UPtH",
    "SERVER_URL": "http://apm-server:8200",
    "DEBUG": True,
    "CAPTURE_BODY": True,
}

apm = ElasticAPM(app)


class ElasticAPMMiddleware:
    def __init__(self, app, apm):
        self.app = app
        self.apm = apm

    def capture_request_body(self):
        if self.app.config['ELASTIC_APM']['CAPTURE_BODY']:
            if request.content_type == 'application/json':
                request_body = request.get_json()
                elasticapm.set_custom_context({"request_body": request_body})

    def capture_response_body(self, response):
        if self.app.config['ELASTIC_APM']['CAPTURE_BODY']:
            if response.content_type == 'application/json':
                response_body = json.loads(response.data)
                elasticapm.set_custom_context({"response_body": response_body})
