def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def power(base: float, exp: int) -> float:
    if exp < 0:
        raise ValueError("Negative exponents not supported")
    result = 1.0
    for _ in range(exp):
        result *= base
    return result
