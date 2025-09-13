import pytest
from src.program_generator import check_satisfied, time_to_minutes
# The @pytest.mark.parametrize decorator lets us define a list of inputs
# and expected outputs for a single test function.
# It's incredibly efficient for testing functions with clear input/output patterns.

@pytest.mark.parametrize("needed, count, expected", [
    # Test cases are defined as tuples: (input1, input2, expected_output)
    # --- Equality ---
    ("=2", 2, True),
    ("=2", 1, False),
    # --- Less than or equal to ---
    ("<=3", 3, True),
    ("<=3", 2, True),
    ("<=3", 4, False),
    # --- Greater than or equal to ---
    (">=1", 1, True),
    (">=1", 2, True),
    (">=1", 0, False),
    # --- Less than ---
    ("<2", 1, True),
    ("<2", 2, False),
    # --- Greater than ---
    (">0", 1, True),
    (">0", 0, False),
])

def test_check_satisfied_with_various_conditions(needed, count, expected):
    """
    A single, parameterized test that covers all conditions for check_satisfied.
    """
    assert check_satisfied(needed, count) is expected

@pytest.mark.parametrize("time_str, expected_minutes", [
    ("09.30", 570),
    ("12.00", 720),
    ("00.00", 0),
    ("23.59", 1439),
])
def test_time_to_minutes(time_str, expected_minutes):
    """
    Tests the time conversion utility function.
    """
    assert time_to_minutes(time_str) == expected_minutes

