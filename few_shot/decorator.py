import inspect
from typing import Any, Callable, List, Optional
from functools import wraps
from textwrap import dedent

from pydantic import BaseModel

from few_shot.example import Example
from few_shot.formatter import FormatterProtocol, CleanFormatter


class few_shot(BaseModel):
    """
    A Pydantic model representing a decorator for a function, which generates a docstring
    with examples of the function's usage.

    Attributes:
        examples: A list of examples, where each example is a dictionary containing keyword arguments,
                  and the expected output of the function.
        docstring_template: A string template for the docstring. The string "{examples}"
                            in the template will be replaced with the formatted examples.
        example_formatter: An instance of a class implementing the FormatterProtocol,
                           (just the `format` method, taking an `Example`).

    Raises:
        TypeError: If the function being decorated does not have a specific return type hint,
                   or if the arguments or output of an example do not match the function's signature.
    """

    examples: List[Example]
    docstring_template: str = "{examples}"
    example_formatter: FormatterProtocol = CleanFormatter()
    default_format: str = "\n\nExamples:\n\n"
    join_str: str = "\n\n"

    class Config:
        arbitrary_types_allowed = True

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

    def _validate_examples(self, func: Callable) -> None:
        sig = inspect.signature(func)
        for example in self.examples:
            example.check(signature=sig)

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

    def _generate_example_strings(self, func: Callable) -> List[str]:
        sig = inspect.signature(func)
        example_strings = []
        for example in self.examples:
            example_strings.append(
                self.example_formatter.format(example, sig, func.__name__)
            )

        return example_strings
