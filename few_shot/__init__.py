"""few-shot"""
from few_shot.decorator import few_shot
from few_shot.example import Example
from few_shot.formatter import JsonFormatter, ReprFormatter

__all__ = ["few_shot", "Example", "JsonFormatter", "ReprFormatter"]
