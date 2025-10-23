from typing import (
    Any,
    Hashable,
    Iterable,
    TypeVar,
    Generic,
)
from typing_extensions import Literal

# The actual type signature of `sampler` does not seem possible to describe
# with mypy yet. There are two problems:
#
# 1. mypy seems incapable of choosing an overload based on `Literal` types with
#    the same underlying type, which in this case is `str`. So we get these
#    errors trying to type check:
#
#      Overloaded function signatures 1 and 2 overlap with incompatible return types
#      Overloaded function signatures 1 and 3 overlap with incompatible return types
#      Overloaded function signatures 2 and 3 overlap with incompatible return types
#
#    This is because `sampler` has a different return type depending on the
#    content of a string parameter, `output`.
#
# 2. `Ticket` should be a `NamedTuple`, but there's no way to use `NamedTuple`
#    with a `TypeVar`, i.e. via `Generic`. See this:
#    https://stackoverflow.com/questions/50530959/generic-namedtuple-in-python-3-6
#
# So this is what I'd like to do but can't (yet?):
#
#   Id = TypeVar('Id', bound=Hashable)
#
#   class Ticket(NamedTuple, Generic[Id]):
#     ticket_number: str
#     id: Id
#     generation: int
#
#   @overload
#   def sampler(
#     id_list: Iterable[Id],
#     seed: Any,
#     with_replacement: bool = ...,
#     drop: int = ...,
#     take: int = ...,
#     output: Literal['id'] = ...,
#     digits: int = ...,
#   ) -> Iterable[Id]: ...
#
#   @overload
#   def sampler(
#     id_list: Iterable[Id],
#     seed: Any,
#     with_replacement: bool = ...,
#     drop: int = ...,
#     take: int = ...,
#     output: Literal['tuple'] = ...,
#     digits: int = ...,
#   ) -> Iterable[Tuple[str, str, int]]: ...
#   @overload
#
#   def sampler(
#     id_list: Iterable[Id],
#     seed: Any,
#     with_replacement: bool = ...,
#     drop: int = ...,
#     take: int = ...,
#     output: Literal['ticket'] = ...,
#     digits: int = ...,
#   ) -> Iterable[Ticket]: ...
#
# To work around #1 we have to to use a single overload with the `output`
# parameter typed as a union of the possible values and the return type a union
# of the possible return types. This is unfortunate because it means mypy cannot
# infer the correct return type based on the arguments.
#
# For #2, I used the workaround suggested in the SO post to inherit from `tuple`
# instead of `NamedTuple` and to handle the "named" part ourselves, which is a
# bit annoying in an interface file but not as bad as the implmentation.

Id = TypeVar("Id", bound=Hashable)

class Ticket(tuple, Generic[Id]):
    ticket_number: str
    id: Id
    generation: int
    def __new__(cls, ticket_number: str, id: Id, generation: int): ...

def sampler(
    id_list: Iterable[Id],
    seed: Any,
    with_replacement: bool = ...,
    drop: int = ...,
    take: int = ...,
    output: Literal["id", "tuple", "ticket"] = ...,
    digits: int = ...,
) -> Iterable[Id] | Iterable[tuple[str, str, int]] | Iterable[Ticket[Id]]: ...
