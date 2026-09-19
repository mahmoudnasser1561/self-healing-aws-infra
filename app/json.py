from datetime import date

from flask.json.provider import DefaultJSONProvider


class JSONProvider(DefaultJSONProvider):
    sort_keys = False

    @staticmethod
    def default(value):
        if isinstance(value, date):
            return value.isoformat()
        return DefaultJSONProvider.default(value)
