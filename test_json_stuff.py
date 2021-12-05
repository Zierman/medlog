import json
from typing import Any
from unittest import TestCase
from json_stuff import JSONSerializable, NewJSONEncoder, NewJSONDecoder, json_serializable


class TestJSONSerializable(TestCase):
    def test_register_json_serializable(self):
        @json_serializable
        class Point(JSONSerializable):
            @classmethod
            def from_dict(cls, d: dict[str, Any]):
                return Point(**d)

            def to_dict(self) -> dict[str, Any]:
                return self.__dict__

            def __init__(self, x, y):
                self.x, self.y = (x, y)

        p = Point(1, 2)
        p2 = json.loads(json.dumps(p, cls=NewJSONEncoder), cls=NewJSONDecoder)
        self.assertEqual(p.x, p2.x)
        self.assertEqual(p.y, p2.y)
