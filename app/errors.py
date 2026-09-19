from flask import jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


class RequestError(Exception):
    def __init__(self, details):
        super().__init__("validation failed")
        self.details = details


def validation_details(error):
    return [
        {
            "field": ".".join(str(part) for part in item["loc"]) or "body",
            "message": item["msg"].removeprefix("Value error, "),
        }
        for item in error.errors()
    ]


def _validation_response(details):
    return jsonify(error="validation failed", details=details), 422


def register_error_handlers(app):
    @app.errorhandler(RequestError)
    def handle_request_error(error):
        return _validation_response(error.details)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return _validation_response(validation_details(error))

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("unhandled error")
        return jsonify(error="internal server error"), 500
