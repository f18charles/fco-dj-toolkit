from typing import Any, Dict, List, TypeVar, Union

# JSON related type aliases
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, Any]

# Type variable for models in services / selectors
ModelType = TypeVar("ModelType")
