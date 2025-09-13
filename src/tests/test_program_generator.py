from src.program_generator import check_satisfied
import pytest

# Test functions MUST start with the word "test_"
# The function name should describe what it's testing.

def test_check_satisfied_equal_condition():
    """
    Tests the '=' condition in check_satisfied.
    This is a "happy path" test, where everything works as expected.
    """
    # ARRANGE: Set up our inputs
    needed_condition = "=2"
    passing_count = 2
    failing_count = 3

    # ACT: Call the function with our inputs
    pass_result = check_satisfied(needed_condition, passing_count)
    fail_result = check_satisfied(needed_condition, failing_count)

    # ASSERT: Check if the results are what we expect
    assert pass_result is True
    assert fail_result is False

def test_check_satisfied_less_than_or_equal_condition():
    """
    Tests the '<=' condition in check_satisfied.
    """
    # ARRANGE
    needed_condition = "<=3"

    # ACT & ASSERT
    assert check_satisfied(needed_condition, 2) is True  # 2 <= 3
    assert check_satisfied(needed_condition, 3) is True  # 3 <= 3 (edge case)
    assert check_satisfied(needed_condition, 4) is False # 4 is not <= 3

def test_check_satisfied_greater_than_condition():
    """
    Tests the '>' condition in check_satisfied.
    """
    # ARRANGE
    needed_condition = ">1"

    # ACT & ASSERT
    assert check_satisfied(needed_condition, 2) is True  # 2 > 1
    assert check_satisfied(needed_condition, 1) is False # 1 is not > 1 (edge case)
    assert check_satisfied(needed_condition, 0) is False # 0 is not > 1

def test_check_satisfied_invalid_condition_raises_error():
    """
    Tests that our function correctly fails when given bad input.
    This is a "sad path" test.
    """
    # ARRANGE
    bad_condition = "abc2" # This isn't a valid operator
    count = 2

    # ACT & ASSERT
    # We expect a ValueError to happen. pytest helps us check for this.
    # The 'with' block says "I expect the code inside here to crash with a ValueError".
    # If it does, the test passes. If it doesn't crash, the test fails!
    with pytest.raises(ValueError):
        check_satisfied(bad_condition, count)