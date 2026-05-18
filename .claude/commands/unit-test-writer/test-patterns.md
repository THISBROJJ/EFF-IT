# Test Patterns Reference

Canonical test case taxonomy used by the unit-test-writer skill. For each
function or method, generate cases in this order to reach ≥90% coverage.

---

## Core Case Types

### 1. Happy path
The function receives valid, typical input and returns the expected output.
This is always the first test written.

```python
def test_add_two_positive_numbers():
    assert add(2, 3) == 5
```

### 2. Null / empty / zero input
Pass None, empty string, empty list, or 0 depending on the type.
Tests null guards and early-return branches.

```python
def test_add_with_zero():
    assert add(0, 5) == 5

def test_format_empty_string():
    assert format_name("") == ""
```

### 3. Boundary values
Min, max, and off-by-one values for numeric inputs; single-element
collections; maximum-length strings.

```python
def test_clamp_at_minimum():
    assert clamp(value=-1, lo=0, hi=10) == 0

def test_clamp_at_maximum():
    assert clamp(value=11, lo=0, hi=10) == 10

def test_clamp_exactly_at_boundary():
    assert clamp(value=0, lo=0, hi=10) == 0
```

### 4. Expected failure / error case
Pass invalid input and assert the correct exception is raised.
Tests error-handling branches.

```python
def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_parse_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_config("not json")
```

### 5. Branch coverage cases
One test per branch not already covered by types 1–4 above.
Identify branches by reading `if`, `elif`, `else`, `try/except`,
`match/case`, and ternary expressions.

```python
# Branch: negative dividend
def test_divide_negative_dividend():
    assert divide(-10, 2) == -5.0

# Branch: except block
def test_parse_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_config("/nonexistent/path.json")
```

---

## Language-Specific Patterns

### Python (pytest)

```python
import pytest
from mymodule import divide

class TestDivide:
    def test_happy_path(self):
        assert divide(10, 2) == 5.0

    def test_zero_dividend(self):
        assert divide(0, 5) == 0.0

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

    @pytest.mark.parametrize("a,b,expected", [
        (10, 2, 5.0),
        (-10, 2, -5.0),
        (7, 2, 3.5),
    ])
    def test_parametrized(self, a, b, expected):
        assert divide(a, b) == expected
```

### JavaScript / TypeScript (Jest)

```typescript
import { divide } from './calculator';

describe('divide', () => {
  it('returns correct quotient for positive numbers', () => {
    expect(divide(10, 2)).toBe(5);
  });

  it('returns 0 when dividend is 0', () => {
    expect(divide(0, 5)).toBe(0);
  });

  it('throws when divisor is 0', () => {
    expect(() => divide(10, 0)).toThrow('Division by zero');
  });

  it('handles negative numbers', () => {
    expect(divide(-10, 2)).toBe(-5);
  });
});
```

### Go (testing package)

```go
func TestDivide(t *testing.T) {
    t.Run("positive numbers", func(t *testing.T) {
        result, err := Divide(10, 2)
        if err != nil { t.Fatal(err) }
        if result != 5 { t.Errorf("got %v, want 5", result) }
    })

    t.Run("zero dividend", func(t *testing.T) {
        result, err := Divide(0, 5)
        if err != nil { t.Fatal(err) }
        if result != 0 { t.Errorf("got %v, want 0", result) }
    })

    t.Run("division by zero returns error", func(t *testing.T) {
        _, err := Divide(10, 0)
        if err == nil { t.Fatal("expected error, got nil") }
    })
}
```

---

## Coverage Checklist

Before marking a function complete, verify:

- [ ] Happy path test exists
- [ ] Null/zero/empty input test exists (if applicable)
- [ ] At least one boundary value test exists (if applicable)
- [ ] At least one error/exception test exists (if the function can error)
- [ ] Every `if`/`else` branch has at least one test each
- [ ] Every `except`/`catch` block has at least one test
- [ ] No existing tests were deleted or modified
