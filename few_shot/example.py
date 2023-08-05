from typing import Tuple, Dict, Any

from pydantic import BaseModel, Field


class Example(BaseModel):
    """
    A Pydantic model representing an example for a function.

    Attributes:
        args: A tuple representing the positional arguments that the function is called with.
        kwargs: A dictionary representing the keyword arguments that the function is called with.
        output: The expected output of the function when called with the above arguments.

    Raises:
        ValidationError: If the input data cannot be parsed into the required types.
    """

    args: Tuple[Any, ...] = Field(...)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    output: Any = Field(...)
