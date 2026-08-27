from dataclasses import dataclass
from datetime import datetime


# -------------------------------------------------------
#                 VALIDATION RESULTS
# -------------------------------------------------------

@dataclass
class WordCountChange:
    mode: str
    value: int
    difference: int
    new_total: int


# -------------------------------------------------------
#                 INTEGER VALIDATION
# -------------------------------------------------------

def parse_non_negative_integer(
    value: str,
    field_name: str
):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a number."

    if parsed < 0:
        return None, f"{field_name} cannot be negative."

    return parsed, None


def parse_positive_integer(
    value: str,
    field_name: str
):
    parsed, error = parse_non_negative_integer(
        value,
        field_name
    )

    if error:
        return None, error

    if parsed == 0:
        return None, f"{field_name} must be greater than 0."

    return parsed, None


# -------------------------------------------------------
#                 WORD COUNT VALIDATION
# -------------------------------------------------------

def validate_word_count_change(
    new_total_value: str,
    difference_value: str,
    initial_total: int
):
    new_total_value = (new_total_value or "").strip()
    difference_value = (difference_value or "").strip()

    if not new_total_value and not difference_value:
        return None, "Pick one option."

    if new_total_value and difference_value:
        return None, "Pick only one option."

    if new_total_value:
        new_total, error = parse_non_negative_integer(
            new_total_value,
            "New total"
        )
        if error:
            return None, error

        return WordCountChange(
            mode="total",
            value=new_total,
            difference=new_total - initial_total,
            new_total=new_total
        ), None

    try:
        difference = int(difference_value)
    except (TypeError, ValueError):
        return None, "Word count change must be a number like +234 or -120."

    new_total = initial_total + difference
    if new_total < 0:
        return None, "That change would make your total word count negative."

    return WordCountChange(
        mode="difference",
        value=difference,
        difference=difference,
        new_total=new_total
    ), None


# -------------------------------------------------------
#                 DATE VALIDATION
# -------------------------------------------------------

def parse_date_only(
    value: str
):
    value = (value or "").strip()
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%d-%m-%Y"
        ).strftime("%d-%m-%Y")
    except ValueError:
        return False
