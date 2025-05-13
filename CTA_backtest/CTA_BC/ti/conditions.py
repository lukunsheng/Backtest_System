import pandas as pd
import numpy as np
from typing import Callable, Any, List, Dict, Union, Optional

class Condition:
    def __init__(self, value_getter: Callable[[pd.DataFrame], Any]):
        self.value_getter = value_getter
        
    def is_above(self, other: Union[float, Callable[[pd.DataFrame], Any]]) -> 'Condition':
        other_getter = other if callable(other) else lambda _: other
        return CompositeCondition(self, other_getter, lambda x, y: x > y)
    
    def is_below(self, other: Union[float, Callable[[pd.DataFrame], Any]]) -> 'Condition':
        other_getter = other if callable(other) else lambda _: other
        return CompositeCondition(self, other_getter, lambda x, y: x < y)
    
    def equals(self, other: Union[float, Callable[[pd.DataFrame], Any]]) -> 'Condition':
        other_getter = other if callable(other) else lambda _: other
        return CompositeCondition(self, other_getter, lambda x, y: x == y)
    
    def has_crossed_above(self, other: Union[float, Callable[[pd.DataFrame], Any]]) -> 'Condition':
        other_getter = other if callable(other) else lambda _: other
        return CrossCondition(self, other_getter, 'above')
    
    def has_crossed_below(self, other: Union[float, Callable[[pd.DataFrame], Any]]) -> 'Condition':
        other_getter = other if callable(other) else lambda _: other
        return CrossCondition(self, other_getter, 'below')
    
    def is_increasing(self, periods: int = 1) -> 'Condition':
        return TrendCondition(self, periods, 'increasing')
    
    def is_decreasing(self, periods: int = 1) -> 'Condition':
        return TrendCondition(self, periods, 'decreasing')
    
    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        return self.value_getter(data)

class CompositeCondition(Condition):
    def __init__(self, condition1: Condition, condition2: Callable, comparator: Callable):
        self.condition1 = condition1
        self.condition2 = condition2
        self.comparator = comparator
        super().__init__(self._evaluate)
        
    def _evaluate(self, data: pd.DataFrame) -> pd.Series:
        value1 = self.condition1.evaluate(data)
        value2 = self.condition2(data) if callable(self.condition2) else self.condition2
        return self.comparator(value1, value2)

class CrossCondition(Condition):
    def __init__(self, condition1: Condition, condition2: Callable, direction: str):
        self.condition1 = condition1
        self.condition2 = condition2
        self.direction = direction
        super().__init__(self._evaluate)
        
    def _evaluate(self, data: pd.DataFrame) -> pd.Series:
        value1 = self.condition1.evaluate(data)
        value2 = self.condition2(data) if callable(self.condition2) else self.condition2
        
        if isinstance(value1, pd.Series) and len(value1) >= 2:
            if self.direction == 'above':
                return (value1.shift(1) <= value2.shift(1)) & (value1 > value2)
            else:
                return (value1.shift(1) >= value2.shift(1)) & (value1 < value2)
        return pd.Series(False, index=data.index)

class TrendCondition(Condition):
    def __init__(self, condition: Condition, periods: int, direction: str):
        self.condition = condition
        self.periods = periods
        self.direction = direction
        super().__init__(self._evaluate)
        
    def _evaluate(self, data: pd.DataFrame) -> pd.Series:
        value = self.condition.evaluate(data)
        
        if self.direction == 'increasing':
            return value.diff(self.periods) > 0
        else:
            return value.diff(self.periods) < 0

class LogicalCondition(Condition):
    def __init__(self, conditions: List[Condition], operator: str):
        self.conditions = conditions
        self.operator = operator
        super().__init__(self._evaluate)
        
    def _evaluate(self, data: pd.DataFrame) -> pd.Series:
        results = [condition.evaluate(data) for condition in self.conditions]
        
        if not results:
            return pd.Series(False, index=data.index)
            
        if self.operator == 'and':
            result = results[0]
            for r in results[1:]:
                result = result & r
            return result
        elif self.operator == 'or':
            result = results[0]
            for r in results[1:]:
                result = result | r
            return result
        elif self.operator == 'not':
            return ~results[0]
        
        return pd.Series(False, index=data.index)

def when(value_getter: Callable[[pd.DataFrame], Any]) -> Condition:
    return Condition(value_getter)

def price(column: str = 'close') -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: df[column]

def volume() -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: df['volume']

def and_(*conditions: Condition) -> Condition:
    return LogicalCondition(list(conditions), 'and')

def or_(*conditions: Condition) -> Condition:
    return LogicalCondition(list(conditions), 'or')

def not_(condition: Condition) -> Condition:
    return LogicalCondition([condition], 'not') 