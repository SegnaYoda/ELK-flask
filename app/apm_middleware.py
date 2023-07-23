import json
import elasticapm
from flask import request, current_app

class ElasticAPMMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Сохраняем информацию о запросе в транзакции
            with elasticapm.capture_span('request', 'request'):
                elasticapm.set_context({
                    'request': {
                        'method': request.method,
                        'url': request.url,
                        'body': request.data,
                        'headers': dict(request.headers),
                    }
                })

            response = self.app(environ, start_response)

            # Сохраняем информацию о ответе в транзакции
            with elasticapm.capture_span('response', 'response'):
                elasticapm.set_context({
                    'response': {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                    }
                })

            return response

        return self.app(environ, custom_start_response)

def init_app(app):
    app.wsgi_app = ElasticAPMMiddleware(app.wsgi_app)
