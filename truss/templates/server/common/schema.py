from types import MappingProxyType
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Generator,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

import pydantic as user_pydantic

try:
    import pydantic.v1 as pydantic_v1
except ImportError:
    import pydantic as pydantic_v1


class OutputType(pydantic_v1.BaseModel):
    type: Optional[type]
    supports_streaming: bool


class TrussSchema(pydantic_v1.BaseModel):
    input_type: Type[user_pydantic.BaseModel]
    output_type: Optional[Type[user_pydantic.BaseModel]]
    supports_streaming: bool

    @classmethod
    def from_signature(
        cls, input_parameters: MappingProxyType, output_annotation: Any
    ) -> Optional["TrussSchema"]:
        """
        Create a TrussSchema from a function signature if annotated, else returns None
        """

        input_type = _parse_input_type(input_parameters)
        print("input_type: ", input_type)
        output_type = _parse_output_type(output_annotation)
        print("output_type :", output_type)

        if not input_type or not output_type:
            return None

        return cls(
            input_type=input_type,
            output_type=output_type.type,
            supports_streaming=output_type.supports_streaming,
        )

    def serialize(self) -> dict:
        """
        Serialize the TrussSchema to a dict. This can then be used for
        generating an OpenAPI spec for this Truss.
        """
        return {
            "input_schema": self.input_type.schema(),
            "output_schema": (
                self.output_type.schema() if self.output_type is not None else None
            ),
            "supports_streaming": self.supports_streaming,
        }


def _parse_input_type(input_parameters: MappingProxyType) -> Optional[type]:
    parameter_types = list(input_parameters.values())
    print("parameter_types: ", parameter_types)

    if len(parameter_types) > 1:
        return None

    input_type = parameter_types[0].annotation
    print("input_type :", input_type)

    if _annotation_is_pydantic_model(input_type):
        print("retuning type.")
        return input_type

    return None


def _annotation_is_pydantic_model(annotation: Any) -> bool:
    # This try/except clause a workaround for the fact that issubclass()
    # does not work with generic types (ie: list, dict),
    # and raises a TypeError
    print("annotation: ", annotation)
    try:
        x = issubclass(annotation, user_pydantic.BaseModel)
        print("bool: ", x)
        return x
    except TypeError:
        return False


def _parse_output_type(output_annotation: Any) -> Optional[OutputType]:
    """
    Therea are 4 possible cases for output_annotation:
    1. Data object -- represented by a Pydantic BaseModel
    2. Streaming -- represented by a Generator or AsyncGenerator
    3. Async -- represented by an Awaitable
    4. Streaming or data object -- it is possible for a function to return both
       a data object and a streaming object. This is represented by a Union of
       a Pydantic BaseModel and a Generator or AsyncGenerator

    If the output_annotation does not match one of these cases, returns None
    """
    if _annotation_is_pydantic_model(output_annotation):
        return OutputType(type=output_annotation, supports_streaming=False)

    if _is_generator_type(output_annotation):
        return OutputType(type=None, supports_streaming=True)

    if _is_awaitable_type(output_annotation):
        output_type = retrieve_base_class_from_awaitable(output_annotation)
        if not output_type:
            return None
        return OutputType(type=output_type, supports_streaming=False)

    if _is_union_type(output_annotation):
        output_type = retrieve_base_class_from_union(output_annotation)
        if not output_type:
            return None
        return OutputType(type=output_type, supports_streaming=True)

    return None


def _is_generator_type(annotation: Any) -> bool:
    base_type = get_origin(annotation)
    return isinstance(base_type, type) and issubclass(
        base_type, (Generator, AsyncGenerator)
    )


def _is_union_type(annotation: Any) -> bool:
    return get_origin(annotation) == Union


def _is_awaitable_type(annotation: Any) -> bool:
    base_type = get_origin(annotation)
    return isinstance(base_type, type) and issubclass(base_type, Awaitable)


def retrieve_base_class_from_awaitable(
    awaitable_annotation: type,
) -> Optional[Type[user_pydantic.BaseModel]]:
    """
    Returns the base class of an Awaitable type if it is of the form:
    Awaitable[PydanticBaseModel]

    Else, returns None
    """
    (awaitable_type,) = get_args(
        awaitable_annotation
    )  # Note that Awaitable has only one type argument
    if isinstance(awaitable_type, type) and issubclass(
        awaitable_type, user_pydantic.BaseModel
    ):
        return awaitable_type

    return None


def _extract_pydantic_base_models(
    union_args: tuple,
) -> List[Type[user_pydantic.BaseModel]]:
    """
    Extracts any pydantic base model arguments from the arms of a Union type.
    The two cases are:
    1. Union[PydanticBaseModel, Generator]
    2. Union[Awaitable[PydanticBaseModel], AsyncGenerator]
    So for Awaitables, we need to extract the base class from the Awaitable type
    """
    return [
        retrieve_base_class_from_awaitable(arg) if _is_awaitable_type(arg) else arg
        for arg in union_args
        if _is_awaitable_type(arg)
        or (isinstance(arg, type) and issubclass(arg, user_pydantic.BaseModel))
    ]


def retrieve_base_class_from_union(
    union_annotation: type,
) -> Optional[Type[user_pydantic.BaseModel]]:
    """
    Returns the base class of a Union type if it is of the form:
    Union[PydanticBaseModel, Generator] or in the case of async functions:
    Union[Awaitable[PydanticBaseModel], AsyncGenerator]

    Else, returns None
    """
    union_args = get_args(union_annotation)

    if len(union_args) != 2:
        return None

    pydantic_base_models = _extract_pydantic_base_models(union_args)
    generators = [arg for arg in union_args if _is_generator_type(arg)]

    if len(pydantic_base_models) != 1 or len(generators) != 1:
        return None

    return pydantic_base_models[0]
