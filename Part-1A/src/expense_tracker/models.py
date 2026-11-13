"""The values the library passes around. All are immutable."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class Expense:
    id: int
    amount_paise: int
    category: str
    date: str
    description: str


@dataclass(frozen=True)
class BudgetWarning:
    """The `budget-exceeded` warning of the specification (FR-013)."""

    category: str
    month: str
    total_paise: int
    limit_paise: int


@dataclass(frozen=True)
class Store:
    expenses: tuple[Expense, ...]
    budgets: Mapping[str, int]
    next_id: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "budgets", MappingProxyType(dict(self.budgets)))

    @classmethod
    def empty(cls) -> "Store":
        return cls((), {}, 1)


@dataclass(frozen=True)
class Outcome:
    store: Store
    expense: Expense
    warnings: tuple[BudgetWarning, ...] = field(default=())
