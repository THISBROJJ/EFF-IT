# Intentionally incomplete — covers only add and subtract.
# unit-test-writer should detect multiply, divide, and power are untested
# and generate tests to bring coverage to ≥90%.

import pytest
from src.calculator import add, subtract


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_add_with_zero():
    assert add(0, 5) == 5


def test_subtract_positive_numbers():
    assert subtract(10, 4) == 6


def test_subtract_resulting_in_negative():
    assert subtract(3, 7) == -4
