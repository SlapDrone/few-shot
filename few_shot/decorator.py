import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Type 
from functools import wraps
from textwrap import dedent

from pydantic import BaseModel, Field, parse_obj_as, validator

from few_shot.example import Example
from few_shot.formatter import FormatterProtocol, ReprFormatter, JsonFormatter


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
    examples: List[Any]
    docstring_template: str = "{examples}"
    example_formatter: FormatterProtocol = ReprFormatter()

    class Config:
        arbitrary_types_allowed = True

    @validator('examples', pre=True)
    def _convert_to_example(cls, examples):
        return [Example(args=ex[0] if isinstance(ex[0], tuple) else (ex[0],), kwargs={}, output=ex[1]) if len(ex) == 2 else Example(*ex) for ex in examples]


    def __call__(self, func: Callable) -> Callable:
        self._validate_return_type(func)
        self._validate_examples(func)
        example_strings = self._generate_example_strings()
    
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
    
        if func.__doc__:
            wrapper.__doc__ = dedent(func.__doc__).format(examples="\n".join(example_strings))
        else:
            wrapper.__doc__ = self.docstring_template.format(examples="\n".join(example_strings))
        return wrapper

    def _validate_return_type(self, func: Callable):
        sig = inspect.signature(func)
        if sig.return_annotation is inspect.Signature.empty or sig.return_annotation is Any:
            raise TypeError("Function must have a specific return type hint")

    def _validate_examples(self, func: Callable):
        sig = inspect.signature(func)
        for example in self.examples:
            if isinstance(example, Tuple):
                if len(example) == 2:
                    example = Example(args=example[0], output=example[1])
                elif len(example) == 3:
                    example = Example(args=example[0], kwargs=example[1], output=example[2])
    
            self._check_argument_types(example.args, sig.parameters.values())
            self._check_keyword_argument_types(example.kwargs, sig.parameters)
            self._check_output_type(example.output, sig.return_annotation)

    def _check_argument_types(self, args: Tuple[Any, ...], hints: List[inspect.Parameter]):
        for arg, hint in zip(args, hints):
            if hint.annotation is inspect.Parameter.empty or hint.annotation is Any:
                raise TypeError(f"Parameter '{hint.name}' must have a specific type hint")
            try:
                parse_obj_as(hint.annotation, arg)
            except Exception as e:
                raise TypeError(f"Expected argument of type {hint.annotation}, got {type(arg)}") from e

    def _check_keyword_argument_types(self, kwargs: Dict[str, Any], hints: Dict[str, inspect.Parameter]):
        for name, value in kwargs.items():
            hint = hints.get(name)
            if hint is None or hint.annotation is inspect.Parameter.empty or hint.annotation is Any:
                raise TypeError(f"Parameter '{name}' must have a specific type hint")
            try:
                parse_obj_as(hint.annotation, value)
            except Exception as e:
                raise TypeError(f"Expected keyword argument '{name}' of type {hint.annotation}, got {type(value)}") from e

    def _check_output_type(self, output: Any, hint: Type[Any]):
        try:
            parse_obj_as(hint, output)
        except Exception as e:
            raise TypeError(f"Expected output of type {hint}, got {type(output)}") from e

    def _serialize_value(self, value):
        if isinstance(value, BaseModel):
            return value.json()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value
            
    def _generate_example_strings(self):
        example_strings = []
        for example in self.examples:
            if isinstance(example, Tuple):
                if len(example) == 2:
                    example = Example(args=example[0], output=example[1])
                elif len(example) == 3:
                    example = Example(args=example[0], kwargs=example[1], output=example[2])
            example_strings.append(self.example_formatter.format(example))

        return example_strings




# alice = Person(name="alice", age=22, cars=[Car(model="mini", speed = 180)])
# bob = Person(name="bob", age=53, cars=[Car(model="ford", speed=200), Car(model="renault", speed=210)])

# @few_shot(
#     examples=[
#         (alice, [Car(model='inim', speed=180.0)]),
#         (bob, [Car(model='drof', speed=200.0), Car(model='tluaner', speed=210.0)]),
#     ],
#     example_formatter=ExampleFormatter(format_type="repr")
# )
# def backwards_cars(p: Person) -> list[Car]:
#     """\
#     Turns all your cars' names backwards every time, guaranteed!

#     Examples:
#     {examples}
#     """
#     return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]
