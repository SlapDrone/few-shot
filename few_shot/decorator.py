import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, ValuesView, Mapping
from functools import wraps
from textwrap import dedent

from pydantic import BaseModel, parse_obj_as, validator

from few_shot.example import Example
from few_shot.formatter import FormatterProtocol, JsonFormatter


class few_shot(BaseModel):
    """
    A Pydantic model representing a decorator for a function, which generates a docstring
    with examples of the function's usage.

    Attributes:
        examples: A list of examples, where each example is a tuple containing arguments,
                  keyword arguments, and the expected output of the function.
        docstring_template: A string template for the docstring. The string "{examples}"
                            in the template will be replaced with the formatted examples.
        example_formatter: An instance of a class implementing the FormatterProtocol,
                           (just the `format` method, taking an `Example`).

    Raises:
        TypeError: If the function being decorated does not have a specific return type hint,
                   or if the arguments or output of an example do not match the function's signature.
    """

    examples: List
    docstring_template: str = "{examples}"
    example_formatter: FormatterProtocol = JsonFormatter()
    default_format: str = "\nExamples:\n"
    join_str: str = "\n"

    class Config:
        arbitrary_types_allowed = True

    @validator("examples", pre=True)
    def _convert_to_example(cls, examples: List[Any]) -> List[Example]:
        return [
            Example(
                args=ex[0] if isinstance(ex[0], tuple) else (ex[0],),
                kwargs=ex[1] if len(ex) > 2 else {},
                output=ex[-1],
            )
            for ex in examples
        ]

    def __call__(self, func: Callable) -> Callable:
        self._validate_return_type(func)
        self._validate_examples(func)
        example_strings = self._generate_example_strings(func)

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:  # type: ignore
            return func(*args, **kwargs)

        if example_strings:  # Only modify docstring if there are examples
            examples_doc = self.join_str.join(example_strings)
            wrapper.__doc__ = self._modify_docstring(func.__doc__, examples_doc)
        return wrapper

    def _modify_docstring(self, doc: Optional[str], examples: str) -> str:
        examples = dedent(examples).lstrip()  # remove leading whitespace
        if doc:
            doc = dedent(doc).lstrip()  # Dedent the existing docstring and ^
            if "{examples}" in doc:
                # Replace {examples} with actual examples
                return doc.format(examples=examples)
            else:
                # Append default_format and examples to existing docstring
                return doc + self.default_format + examples
        else:
            # Create a new docstring with default_format and examples
            return (self.default_format + examples).lstrip()

    def _validate_return_type(self, func: Callable) -> None:
        sig = inspect.signature(func)
        if (
            sig.return_annotation is inspect.Signature.empty
            or sig.return_annotation is Any
        ):
            raise TypeError("Function must have a specific return type hint")

    def _validate_examples(self, func: Callable) -> None:
        sig = inspect.signature(func)
        for example in self.examples:
            if isinstance(example, tuple):
                if len(example) == 2:
                    example = Example(args=example[0], output=example[1])
                elif len(example) == 3:
                    example = Example(
                        args=example[0], kwargs=example[1], output=example[2]
                    )

            self._check_argument_types(example.args, sig.parameters.values())
            self._check_keyword_argument_types(example.kwargs, sig.parameters)
            self._check_output_type(example.output, sig.return_annotation)

    def _check_argument_types(
        self, args: Tuple[Any, ...], hints: ValuesView[inspect.Parameter]
    ) -> None:
        for arg, hint in zip(args, hints):
            if hint.annotation is inspect.Parameter.empty or hint.annotation is Any:
                raise TypeError(
                    f"Parameter '{hint.name}' must have a specific type hint"
                )
            try:
                parse_obj_as(hint.annotation, arg)
            except Exception as e:
                raise TypeError(
                    f"Expected argument of type {hint.annotation}, got {type(arg)}"
                ) from e

    def _check_keyword_argument_types(
        self, kwargs: Dict[str, Any], hints: Mapping[str, inspect.Parameter]
    ) -> None:
        for name, value in kwargs.items():
            hint = hints.get(name)
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

    def _generate_example_strings(self, func: Callable) -> List[str]:
        sig = inspect.signature(func)
        example_strings = []
        for example in self.examples:
            if isinstance(example, tuple):
                if len(example) == 2:
                    example = Example(args=example[0], output=example[1])
                elif len(example) == 3:
                    example = Example(
                        args=example[0], kwargs=example[1], output=example[2]
                    )
            example_strings.append(self.example_formatter.format(example, sig))

        return example_strings
