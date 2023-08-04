
import json
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from few_shot.example import Example


@runtime_checkable
class FormatterProtocol(Protocol):
    def format(self, example: Example):
        ...


class JsonFormatter:
    def format(self, example: Example):
        try:
            args_str = json.dumps(self._serialize_value(example.args))
            kwargs_str = json.dumps(self._serialize_value(example.kwargs))
            output_str = json.dumps(self._serialize_value(example.output))
        except TypeError as e:
            raise TypeError("All arguments, keyword arguments, and outputs must be JSON serializable") from e
        return f"{args_str}, {kwargs_str} -> {output_str}"

    def _serialize_value(self, value):
        if isinstance(value, BaseModel):
            return value.json()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value


class ReprFormatter:
    def format(self, example: Example):
        return f"{repr(example.args)}, {repr(example.kwargs)} -> {repr(example.output)}"
