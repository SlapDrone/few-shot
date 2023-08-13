import inspect
from typing import Tuple, Dict, Any, Mapping, Type

from pydantic import BaseModel, Field, root_validator


class Example(BaseModel):
    """
    A Pydantic model representing an example for a function.

    Attributes:
        kwargs: A dictionary representing the keyword arguments that the function is called with.
        output: The expected output of the function when called with the above arguments.

    Raises:
        ValidationError: If the input data cannot be parsed into the required types.
    """
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    output: Any = Field(...)

    @root_validator(pre=True)
    def split_args_kwargs_output(cls, values):
        output = values.pop('output')
        kwargs = values
        return {'kwargs': kwargs, 'output': output}

    def check(self, signature: inspect.Signature) -> None:
        print(f"{self}")
        print("example kwargs: ", self.kwargs)
        self._check_keyword_argument_types(self.kwargs, signature.parameters)
        self._check_output_type(self.output, signature.return_annotation)

    def _check_keyword_argument_types(
        self, kwargs: Dict[str, Any], hints: Mapping[str, inspect.Parameter]
    ) -> None:
        for name, value in kwargs.items():
            hint = hints.get(name)
            print(f"{name=}, {value=}, {hint=}")
            if (
                hint is None
                or hint.annotation is inspect.Parameter.empty
                or hint.annotation is Any
            ):
                raise TypeError(f"Parameter '{name}' must have a specific type hint")
            try:
                parse_obj_as(hint.annotation, value)
            except Exception as e:
                raise TypeError(
                    f"Expected keyword argument '{name}' of type {hint.annotation}, got {type(value)}"
                ) from e

    def _check_output_type(self, output: Any, hint: Type[Any]) -> None:
        try:
            parse_obj_as(hint, output)
        except Exception as e:
            raise TypeError(
                f"Expected output of type {hint}, got {type(output)}"
            ) from e