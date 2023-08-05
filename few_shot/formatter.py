import inspect
import json
from typing import Protocol, runtime_checkable, Optional, Any

from pydantic import BaseModel

from few_shot.example import Example


@runtime_checkable
class FormatterProtocol(Protocol):
    def format(self, example: Example, sig: inspect.Signature) -> str:
        ...


class JsonFormatter:
    def format(self, example: Example, sig: inspect.Signature) -> str:
        try:
            args_dict = {
                name: self._serialize_value(arg)
                for name, arg in zip(sig.parameters.keys(), example.args)
            }
            if example.kwargs:  # Only include kwargs if it's not empty
                args_dict.update(
                    {
                        name: self._serialize_value(value)
                        for name, value in example.kwargs.items()
                    }
                )
            args_str = json.dumps(args_dict)
            output_str = json.dumps(self._serialize_value(example.output))
        except TypeError as e:
            raise TypeError(
                "All arguments, keyword arguments, and outputs must be JSON serializable"
            ) from e
        return f"{args_str} -> {output_str}"

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.dict()  # return a dict instead of a JSON string
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value


class ReprFormatter:
    def format(self, example: Example, sig: Optional[inspect.Signature] = None) -> str:
        return f"{repr(example.args)}, {repr(example.kwargs)} -> {repr(example.output)}"
