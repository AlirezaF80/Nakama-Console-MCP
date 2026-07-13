"""Validate strict tool response envelopes at the handler boundary."""

from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dump_envelope(model: Type[T], data: Any) -> dict[str, Any]:
    return model.model_validate(data).model_dump()


__all__ = ["dump_envelope"]
