// Intentionally incomplete — covers only add and subtract.
// unit-test-writer should detect multiply, divide, and power are untested
// and generate tests to bring coverage to ≥90%.

const { add, subtract } = require('./calculator');

describe('add', () => {
  it('returns the sum of two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  it('returns the correct value when adding zero', () => {
    expect(add(0, 5)).toBe(5);
  });
});

describe('subtract', () => {
  it('returns the difference of two numbers', () => {
    expect(subtract(10, 4)).toBe(6);
  });

  it('returns a negative result when minuend is smaller', () => {
    expect(subtract(3, 7)).toBe(-4);
  });
});
