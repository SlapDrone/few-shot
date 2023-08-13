import inspect
from typing import Dict, Any, Mapping, Type

from pydantic import BaseModel, Field, root_validator, parse_obj_as

from few_shot.exceptions import InvalidParameter


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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  #  type: ignore

    @root_validator(pre=True)
    def split_args_kwargs_output(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        output = values.pop("output")
        return {"kwargs": values, "output": output}

    def check(self, signature: inspect.Signature) -> None:
        self._check_keyword_argument_types(self.kwargs, signature.parameters)
        self._check_output_type(self.output, signature.return_annotation)

    def _check_keyword_argument_types(
        self, kwargs: Dict[str, Any], hints: Mapping[str, inspect.Parameter]
    ) -> None:
        var_keyword_hint = None
        for name, param in hints.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                var_keyword_hint = param.annotation
                break

        for name, value in kwargs.items():
            hint = hints.get(name)
            if (
                hint is None
                or hint.annotation is inspect.Parameter.empty
                or hint.annotation is Any
            ):
                if var_keyword_hint is not None:
                    # If the function accepts **kwargs, use the type hint from **kwargs
                    hint = var_keyword_hint
                else:
                    raise InvalidParameter(
                        f"Parameter '{name}' does not match a type hinted parameter"
                    )
            try:
                # Use hint.annotation if hint is an inspect.Parameter, otherwise use hint
                type_hint = (
                    hint.annotation if isinstance(hint, inspect.Parameter) else hint
                )
                parse_obj_as(type_hint, value)
            except Exception as e:
                raise TypeError(
                    f"Expected keyword argument '{name}' of type {hint}, got {type(value)}"
                ) from e

    def _check_output_type(self, output: Any, hint: Type[Any]) -> None:
        try:
            parse_obj_as(hint, output)
        except Exception as e:
            raise TypeError(
                f"Expected output of type {hint}, got {type(output)}"
            ) from e
