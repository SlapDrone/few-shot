# Few shot

Few shot is a Python package that provides a lightweight, framework-independent way of enriching function docstrings programmatically with examples. Y'know, since functions are prompts now.

It has very minimal dependencies, although it was designed with use alongside LLM function-calling libraries such as [marvin](https://www.askmarvin.ai/), [llama index](https://github.com/jerryjliu/llama_index), [openai function call](https://github.com/jxnl/openai_function_call) or [langchain](https://github.com/langchain-ai/langchain) in mind.

**As it stands, this was written in an evening with a particular project in mind. If it is (or could be, with some tweaks) useful to you, feedback and contributions are more than welcome.**

## Example

Here's an example of using `few_shot` with marvin:

```python
from few_shot import few_shot, JsonFormatter
from pydantic import BaseModel
import marvin

class Car(BaseModel):
    model: str
    speed: float

class Person(BaseModel):
    name: str
    age: int
    cars: list[Car]

@marvin.ai_fn
@few_shot(
    examples=[
        ((Person(name="alice", age=22, cars=[Car(model="mini", speed = 180)]),),  [Car(model='inim', speed=180.0)]),
        ((Person(name="bob", age=53, cars=[Car(model="ford", speed=200), Car(model="renault", speed=210)]),),  [Car(model='drof', speed=200.0), Car(model='tluaner', speed=210.0)]),
    ],
    example_formatter=JsonFormatter()
)
def generate_backwards_car_names(person: Person, **kwargs) -> list[Car]:
    """
    Given a person, return a list of their cars with the model names backwards.
    """
    pass

print(generate_backwards_car_names.description)
```

    Given a person, return a list of their cars with the model names backwards.

    Examples:
    {"person": {"name": "alice", "age": 22, "cars": [{"model": "mini", "speed": 180.0}]}} -> [{"model": "inim", "speed": 180.0}]
    {"person": {"name": "bob", "age": 53, "cars": [{"model": "ford", "speed": 200.0}, {"model": "renault", "speed": 210.0}]}} -> [{"model": "drof", "speed": 200.0}, {"model": "tluaner", "speed": 210.0}]

In the example above, the `generate_backwards_car_names` function is an AI function defined using Marvin's `ai_fn` decorator. The function's body is empty, as the actual implementation is provided by the AI. The `few_shot` decorator enriches the function's docstring with examples of its usage, formatted as JSON.

```python
clara = Person(name="clara", age=38, cars=[Car(model="delorean", speed=88.), Car(model="T", speed=20.)])
generate_backwards_car_names(clara)
```
    [Car(model='naroled', speed=88.0), Car(model='T', speed=20.0)]

## Features

- Generate docstrings with examples of the function's usage.
- Validate function's arguments and output with the examples provided.
- Supports Pydantic models for complex data structures.
- Supports JSON and repr formatting for examples in docstrings out of the box, but can be easily extended. PRs welcome :3!

## Installation

The package is managed as a poetry project in `pyproject.toml`.

To install Few_Shot, you can use pip:

```sh
pip install few-shot
```

Or, if you are a person of culture, add it to your [poetry](https://python-poetry.org/) project:

```sh
poetry add few-shot
```

## Usage

The main feature of Few_Shot is the `few_shot` decorator. This decorator takes a function and a set of examples, and generates a docstring for the function that includes these examples. The examples are validated against the function's signature and return type, ensuring that they are correct. The decorator has several optional arguments that allow you to customize how the examples are formatted and included in the docstring:

- `examples`: A list of examples, where each example is a tuple containing arguments, keyword arguments, and the expected output of the function.
- `example_formatter`: An instance of a class implementing the FormatterProtocol (just the `format` method, taking an `Example`). Default is `ReprFormatter()`.
- `docstring_template`: A string template for the docstring. The string "{examples}" in the template will be replaced with the formatted examples. Default is "{examples}".
- `join_str`: A string used to join multiple example strings in the docstring. Default is "\n".
- `default_format`: A string that is prepended to the examples in the docstring. Default is "\nExamples:\n".


## Testing

To run the tests, execute:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Few_Shot is released under the MIT License.