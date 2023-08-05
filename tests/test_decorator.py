import inspect
import json
from textwrap import dedent 

import pytest
from pydantic import ValidationError, BaseModel
from few_shot import few_shot, JsonFormatter, ReprFormatter, Example


# simple examples
class Car(BaseModel):
    model: str
    speed: float

class Person(BaseModel):
    name: str
    age: int
    cars: list[Car]


@pytest.fixture
def example():
    return Example(args=("test",), kwargs={}, output="output")

@pytest.fixture
def formatter_json():
    return JsonFormatter()

@pytest.fixture
def formatter_repr():
    return ReprFormatter()

def test_example(example):
    assert example.args == ("test",)
    assert example.kwargs == {}
    assert example.output == "output"

    with pytest.raises(ValidationError):
        Example(args="test", kwargs={}, output="output")

def test_json_formatter(formatter_json, example):
    # json serialises tuple as array (i.e. [])
    sig = inspect.signature(lambda test: "output")  # create a dummy function signature
    assert formatter_json.format(example, sig) == '{"test": "test"} -> "output"' 

    with pytest.raises(TypeError):
        formatter_json.format(Example(args=(set(),), kwargs={}, output="output"), sig)


def test_repr_formatter(formatter_repr, example):
    assert formatter_repr.format(example) == "('test',), {} -> 'output'"

def test_few_shot_with_valid_data():
    @few_shot(
        examples=[
            ((Person(name="alice", age=22, cars=[Car(model="mini", speed = 180)]),), {}, [Car(model='inim', speed=180.0)]),
            ((Person(name="bob", age=53, cars=[Car(model="ford", speed=200), Car(model="renault", speed=210)]),), {}, [Car(model='drof', speed=200.0), Car(model='tluaner', speed=210.0)]),
        ],
        example_formatter=JsonFormatter()
    )
    def backwards_cars(p: Person) -> list[Car]:
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {examples}"""
        return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]
    expected_doc = dedent("""\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {"p": {"name": "alice", "age": 22, "cars": [{"model": "mini", "speed": 180.0}]}} -> [{"model": "inim", "speed": 180.0}]
        {"p": {"name": "bob", "age": 53, "cars": [{"model": "ford", "speed": 200.0}, {"model": "renault", "speed": 210.0}]}} -> [{"model": "drof", "speed": 200.0}, {"model": "tluaner", "speed": 210.0}]""")
    assert backwards_cars.__doc__ == expected_doc


def test_few_shot_with_empty_cars_list():
    @few_shot(
        examples=[
            ((Person(name="alice", age=22, cars=[]),), {}, []),
        ],
        example_formatter=JsonFormatter()
    )
    def backwards_cars(p: Person) -> list[Car]:
        """\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {examples}"""
        return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]

    expected_doc = dedent("""\
        Turns all your cars' names backwards every time, guaranteed!

        Examples:
        {"p": {"name": "alice", "age": 22, "cars": []}} -> []""").rstrip()  # remove trailing newline
    assert backwards_cars.__doc__ == expected_doc


def test_few_shot_with_invalid_return_type():
    with pytest.raises(TypeError):
        @few_shot(
            examples=[
                ((Person(name="alice", age=22, cars=[Car(model="mini", speed = 180)]),), {}, [Car(model='inim', speed=180.0)]),
                ((Person(name="bob", age=53, cars=[Car(model="ford", speed=200), Car(model="renault", speed=210)]),), {}, [Car(model='drof', speed=200.0), Car(model='tluaner', speed=210.0)]),
            ],
            example_formatter=JsonFormatter()
        )
        def backwards_cars_no_return_hint(p: Person):
            return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]

def test_few_shot_with_invalid_argument_type():
    with pytest.raises(TypeError):
        @few_shot(
            examples=[
                ((Person(name="alice", age=22, cars=[Car(model="mini", speed = 180)]),), {}, [Car(model='inim', speed=180.0)]),
                ((Person(name="bob", age=53, cars=[Car(model="ford", speed=200), Car(model="renault", speed=210)]),), {}, [Car(model='drof', speed=200.0), Car(model='tluaner', speed=210.0)]),
            ],
            example_formatter=JsonFormatter()
        )
        def backwards_cars_invalid_arg(p: str) -> list[Car]:
            return [Car(model=c.model[::-1], speed=c.speed) for c in p.cars]

def test_few_shot_with_non_serializable_data():
    class NonSerializable:
        pass

    with pytest.raises(TypeError):
        @few_shot(
            examples=[
                ((NonSerializable(),), {}, "output"),
            ],
            example_formatter=JsonFormatter()
        )
        def func_non_serializable(p: NonSerializable) -> str:
            return "output"

def test_few_shot_with_function_with_default_args():
    @few_shot(
        examples=[
            (("test",), {"kwarg": "value"}, "output"),
            (("test2",), {"kwarg": "value2"}, "output2"),
        ],
        example_formatter=JsonFormatter()
    )
    def func_with_default_args(arg: str, kwarg: str = "default") -> str:
        return arg

    assert func_with_default_args("test", "value") == "test"

def test_few_shot_with_function_with_variable_args():
    @few_shot(
        examples=[
            ((1, 2, 3), {}, 6),
            ((4, 5, 6), {}, 15),
        ],
        example_formatter=JsonFormatter()
    )
    def func_with_variable_args(*args: int) -> int:
        return sum(args)

    assert func_with_variable_args(1, 2, 3) == 6
