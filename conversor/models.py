from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

@dataclass
class AccountMeta:
    bank: str
    agency: str = ""
    account: str = ""
    digit: str = ""
    operation: str = ""
    source_format: str = ""
    warnings: list[str] = field(default_factory=list)

@dataclass
class Transaction:
    date: str
    description: str
    document: str = ""
    dc: str = "C"
    value: Decimal = Decimal("0")
    balance: Optional[Decimal] = None

@dataclass
class ConversionResult:
    meta: AccountMeta
    transactions: list[Transaction]
    warnings: list[str] = field(default_factory=list)
