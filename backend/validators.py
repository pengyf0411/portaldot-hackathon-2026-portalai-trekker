"""
validators.py — Input validation for all intent parameters.

Validates SS58 addresses, amount ranges, and required fields before
any chain query or extrinsic construction is attempted.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Portaldot uses ss58_format=42, addresses start with '5'
# SS58 addresses are Base58 encoded, typically 47-48 characters
SS58_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{46,50}$")

# Minimum transfer: 0.000_000_000_000_01 POT (1 planck)
MIN_TRANSFER_POT = 1e-14
# Maximum reasonable transfer per operation (safety guard for demo)
MAX_TRANSFER_POT = 1_000_000.0


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_ss58_address(address: Optional[str], field_name: str = "Address") -> str:
    """Validate that the address is a plausible Portaldot SS58 address."""
    if not address:
        raise ValidationError(
            f"Missing {field_name}. Provide a valid Portaldot SS58 address (starts with '5')."
        )
    address = address.strip()
    if not SS58_PATTERN.match(address):
        raise ValidationError(
            f"Invalid {field_name}: '{address[:20]}...' is not a valid SS58 address "
            f"(should start with '5', about 47–48 characters)."
        )
    return address


def validate_amount_pot(amount: Optional[float], field_name: str = "Amount") -> float:
    """Validate that the transfer amount is a positive, reasonable number."""
    if amount is None:
        raise ValidationError(f"Missing {field_name}. Specify the POT amount.")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a number, got: {amount}")
    if amount < MIN_TRANSFER_POT:
        raise ValidationError(f"{field_name} must be greater than 0 (got {amount} POT).")
    if amount > MAX_TRANSFER_POT:
        raise ValidationError(
            f"{field_name} exceeds the per-transaction limit ({MAX_TRANSFER_POT:,} POT)."
        )
    return amount


def validate_transfer_params(params: dict) -> dict:
    """
    Validate and normalize transfer intent parameters.

    Returns cleaned params dict.
    Raises ValidationError on invalid input.
    """
    to = validate_ss58_address(params.get("to"), "Destination address")
    amount_pot = validate_amount_pot(params.get("amount_pot"), "Transfer amount")
    from_address = params.get("from_address")
    if from_address:
        from_address = validate_ss58_address(from_address, "Sender address")
    return {"to": to, "amount_pot": amount_pot, "from_address": from_address}


def validate_estimate_fee_params(params: dict) -> dict:
    """Validate estimate_fee params. 'to' is optional; 'amount_pot' is required."""
    amount_pot = validate_amount_pot(params.get("amount_pot"), "Amount")
    to = params.get("to")
    if to:
        to = validate_ss58_address(to, "Destination address")
    from_address = params.get("from_address")
    if from_address:
        from_address = validate_ss58_address(from_address, "Sender address")
    return {"to": to, "amount_pot": amount_pot, "from_address": from_address}


def validate_query_balance_params(params: dict) -> dict:
    """Validate query_balance params. Address is optional (uses connected wallet if absent)."""
    address = params.get("address")
    if address:
        address = validate_ss58_address(address, "Query address")
    return {"address": address}


def validate_query_tx_history_params(params: dict) -> dict:
    """Validate query_tx_history params."""
    address = params.get("address")
    if address:
        address = validate_ss58_address(address, "Query address")
    limit = int(params.get("limit", 10))
    limit = max(1, min(limit, 50))  # clamp between 1 and 50
    return {"address": address, "limit": limit}


def validate_query_validators_params(params: dict) -> dict:
    """Validate query_validators params."""
    limit = int(params.get("limit", 10))
    limit = max(1, min(limit, 50))
    return {"limit": limit}
