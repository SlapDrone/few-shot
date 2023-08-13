import inspect
from typing import List, Callable
from textwrap import dedent

import pytest
from pydantic import ValidationError, BaseModel
from few_shot import few_shot, JsonFormatter, CleanFormatter, Example


# simple examples
class Car(BaseModel):
    model: str
    speed: float


class Person(BaseModel):
    name: str
    age: int
    cars: List[Car]


@pytest.fixture
def dummy_fn() -> Callable:
    def dummy(x: str, y: int = 1) -> str:
        return "output"

    return dummy


@pytest.fixture
def example() -> Example:
    return Example(x="test", y=1, output="output")


@pytest.fixture
def formatter_json() -> JsonFormatter:
    return JsonFormatter()


@pytest.fixture
def formatter_clean() -> CleanFormatter:
    return CleanFormatter()


def test_example(example: Example) -> None:
    assert example.kwargs == {"x": "test", "y": 1}
    assert example.output == "output"

    with pytest.raises(ValidationError):
        Example(kwargs="test", output="output")  # type: ignore


def test_json_formatter(
    formatter_json: JsonFormatter, example: Example, dummy_fn: Callable
) -> None:
    sig = inspect.signature(dummy_fn)  # create a dummy function signature
    assert (
        formatter_json.format(example, sig, dummy_fn.__name__)
        == '{"x": "test", "y": 1} -> "output"'
    )

    with pytest.raises(TypeError):
        formatter_json.format(
            Example(kwargs={"x": set()}, output="output"), sig, dummy_fn.__name__
        )


def test_clean_formatter(
    formatter_clean: CleanFormatter, example: Example, dummy_fn: Callable
) -> None:
    sig = inspect.signature(dummy_fn)
    assert (
        formatter_clean.format(example, sig, dummy_fn.__name__)
        == "dummy(x='test', y=1) -> 'output'"
    )


def test_few_shot_with_valid_data() -> None:
    @few_shot(
        examples=[
            Example(
                kwargs={"p": Person(name="alice", age=22, cars=[Car(model="mini", speed=180)])},
                output=[Car(model="inim", speed=180.0)]
            ),
            Example(
                kwargs={"p": Person(
                    name="bob",
                    age=53,
                    cars=[
                        Car(model="ford", speed=200),
                        Car(model="renault", speed=210),
                    ],
                )},
                output=[Car(model="drof", speed=200.0), Car(model="tluaner", speed=210.0)]
            ),
        ],
        example_formatter=JsonFormatter(),
        join_str="\n",
    )
    def backwards_cars(p: Person) -> List[Car]:
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {examples}"""
        return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]

    expected_doc = dedent(
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {"p": {"name": "alice", "age": 22, "cars": [{"model": "mini", "speed": 180.0}]}} -> [{"model": "inim", "speed": 180.0}]
        {"p": {"name": "bob", "age": 53, "cars": [{"model": "ford", "speed": 200.0}, {"model": "renault", "speed": 210.0}]}} -> [{"model": "drof", "speed": 200.0}, {"model": "tluaner", "speed": 210.0}]"""
    )
    assert backwards_cars.__doc__ == expected_doc


def test_few_shot_with_empty_cars_list() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"p": Person(name="alice", age=22, cars=[])}, output=[]),
        ],
        example_formatter=JsonFormatter(),
    )
    def backwards_cars(p: Person) -> List[Car]:
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:

        {examples}"""
        return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]

    expected_doc = dedent(
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:

        {"p": {"name": "alice", "age": 22, "cars": []}} -> []"""
    ).rstrip()  # remove trailing newline
    assert backwards_cars.__doc__ == expected_doc


def test_few_shot_with_invalid_return_type() -> None:
    dec = few_shot(
        examples=[
            Example(
                kwargs={"p": Person(name="alice", age=22, cars=[Car(model="mini", speed=180)])},
                output=[Car(model="inim", speed=180.0)],
            ),
            Example(
                kwargs={"p": Person(
                    name="bob",
                    age=53,
                    cars=[
                        Car(model="ford", speed=200),
                        Car(model="renault", speed=210),
                    ],
                )},
                output=[Car(model="drof", speed=200.0), Car(model="tluaner", speed=210.0)],
            ),
        ],
        example_formatter=JsonFormatter(),
    )
    with pytest.raises(TypeError):

        def backwards_cars_no_return_hint(p: Person):  # type: ignore
            return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]  # type: ignore

        dec(backwards_cars_no_return_hint)

    with pytest.raises(TypeError):

        def backwards_cars_bad_return_hint(p: Person) -> List[Person]:  # type: ignore
            return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]  # type: ignore

        dec(backwards_cars_bad_return_hint)


def test_few_shot_with_invalid_argument_type() -> None:
    with pytest.raises(TypeError):

        @few_shot(
            examples=[
                Example(
                    kwargs={"p": Person(name="alice", age=22, cars=[Car(model="mini", speed=180)])},
                    output=[Car(model="inim", speed=180.0)],
                ),
                Example(
                    kwargs={"p": Person(
                        name="bob",
                        age=53,
                        cars=[
                            Car(model="ford", speed=200),
                            Car(model="renault", speed=210),
                        ],
                    )},
                    output=[Car(model="drof", speed=200.0), Car(model="tluaner", speed=210.0)],
                ),
            ],
            example_formatter=JsonFormatter(),
        )
        def backwards_cars_invalid_arg(p: str) -> List[Car]:  # type: ignore
            return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]  # type: ignore


def test_few_shot_with_non_serializable_data() -> None:
    class NonSerializable:
        pass

    with pytest.raises(TypeError):

        @few_shot(
            examples=[
                Example(kwargs={"p": NonSerializable()}, output="output"),
            ],
            example_formatter=JsonFormatter(),
        )
        def func_non_serializable(p: NonSerializable) -> str:
            return "output"


def test_few_shot_with_function_with_default_args() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"arg": "test", "kwarg": "value"}, output="test"),
            Example(kwargs={"arg": "test2", "kwarg": "value2"}, output="test2"),
        ],
        example_formatter=JsonFormatter(),
    )
    def func_with_default_args(arg: str, kwarg: str = "default") -> str:
        return arg

    assert func_with_default_args("test", "value") == "test"


def test_few_shot_with_function_with_variable_args() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"args": (1, 2, 3)}, output=6),
            Example(kwargs={"args": (4, 5, 6)}, output=15),
        ],
        example_formatter=JsonFormatter(),
    )
    def func_with_variable_args(*args: int) -> int:
        return sum(args)

    assert func_with_variable_args(1, 2, 3) == 6


def test_few_shot_with_no_docstring() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"arg": "test"}, output="output"),
        ],
        example_formatter=JsonFormatter(),
    )
    def func_no_docstring(arg: str) -> str:
        return arg

    expected_doc = dedent(
        """\
    Examples:

    {"arg": "test"} -> "output\""""
    ).rstrip()  # remove trailing newline
    assert func_no_docstring.__doc__ == expected_doc


def test_few_shot_with_no_examples_placeholder() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"arg": "test"}, output="output"),
        ],
        example_formatter=JsonFormatter(),
    )
    def func_no_examples_placeholder(arg: str) -> str:
        """This function does something."""
        return arg

    expected_doc = dedent(
        """\
    This function does something.

    Examples:
    
    {"arg": "test"} -> \"output\""""
    ).rstrip()  # remove trailing newline
    assert func_no_examples_placeholder.__doc__ == expected_doc


def test_few_shot_with_different_formatting_separators() -> None:
    @few_shot(
        examples=[
            Example(kwargs={"arg": "test"}, output="output"),
            Example(kwargs={"arg": "test2"}, output="output2"),
        ],
        example_formatter=JsonFormatter(),
        join_str="\n---\n",
        default_format="\nExample Usage:\n",  # this should be ignored
    )
    def func_different_formatting_separators(arg: str) -> str:
        """
        This function does something.

        {examples}"""
        return arg

    expected_doc = dedent(
        """\
    This function does something.

    {"arg": "test"} -> "output"
    ---
    {"arg": "test2"} -> "output2\""""
    ).rstrip()  # remove trailing newline
    assert func_different_formatting_separators.__doc__ == expected_doc
