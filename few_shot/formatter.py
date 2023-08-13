import inspect
import json
from typing import Protocol, runtime_checkable, Any

from pydantic import BaseModel

from few_shot.example import Example


@runtime_checkable
class FormatterProtocol(Protocol):
    def format(self, example: Example, sig: inspect.Signature, func_name: str) -> str:
        ...


class JsonFormatter(BaseModel):
    template: str = "{inputs} -> {output}"

    def format(self, example: Example, sig: inspect.Signature, func_name: str) -> str:
        try:
            args_dict = {}
            if example.kwargs:
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
        return self.template.format(inputs=args_str, output=output_str)

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.dict()  # return a dict instead of a JSON string
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value


class CleanFormatter(BaseModel):
    template: str = "{name}({inputs}) -> {output}"

    def format(self, example: Example, sig: inspect.Signature, func_name: str) -> str:
        # Bind the arguments and keyword arguments to the signature's parameters
        bound_args = sig.bind(**example.kwargs)
        bound_args.apply_defaults()

        # Format the function call
        params = ", ".join(f"{k}={repr(v)}" for k, v in bound_args.arguments.items())
        return self.template.format(
            name=func_name, inputs=params, output=repr(example.output)
        )
