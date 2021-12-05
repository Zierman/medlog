import functools
import json
from abc import abstractmethod, ABC
from datetime import timedelta
from typing import Any, Callable


class BaseJSONSerializable(ABC):
    @classmethod
    @abstractmethod
    def register_json_serializable(cls):
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict[str, Any]):
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class NewJSONDecoder(json.JSONDecoder):
    registry: dict[str, Callable] = {timedelta.__name__: lambda d: timedelta(**d)}

    def __init__(self, *args, **kwargs):
        fallback = json.JSONDecoder(*args, **kwargs).object_hook

        def new_hook(d: dict[str, Any]) -> Any:
            if '__DECODE_KEY__' in d:
                key = d['__DECODE_KEY__']
                del d['__DECODE_KEY__']
                return self.registry[key](d)
            else:
                return fallback(d)

        kwargs['object_hook'] = new_hook
        super().__init__(*args, **kwargs)


class NewJSONEncoder(json.JSONEncoder):
    registry: dict[type, Callable] = {timedelta: lambda o: {'__DECODE_KEY__': timedelta.__name__,
                                                            'days': o.days,
                                                            'seconds': o.seconds,
                                                            'microseconds': o.microseconds}}

    def default(self, o):
        if isinstance(o, (BaseJSONSerializable, timedelta)):
            return NewJSONEncoder.registry[o.__class__](o)
        else:
            return super().default(o)


class JSONSerializable(BaseJSONSerializable):

    @classmethod
    def register_json_serializable(cls):
        key = cls.__name__

        def new_to_dict(o) -> dict[str, Any]:
            return dict(__DECODE_KEY__=key, **o.to_dict())

        def new_from_dict(d: dict[str, Any]) -> cls:
            return cls.from_dict(d)

        NewJSONEncoder.registry[cls] = new_to_dict
        NewJSONDecoder.registry[key] = new_from_dict


def json_serializable(cls):
    if not issubclass(cls, BaseJSONSerializable):
        raise TypeError(f'{cls.__name__} is not a subclass of {BaseJSONSerializable.__name__}')
    cls.register_json_serializable()
    return cls
