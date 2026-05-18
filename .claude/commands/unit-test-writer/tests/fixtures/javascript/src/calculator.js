function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  return a * b;
}

function divide(a, b) {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
}

function power(base, exp) {
  if (exp < 0) {
    throw new RangeError('Negative exponents not supported');
  }
  return Math.pow(base, exp);
}

module.exports = { add, subtract, multiply, divide, power };
