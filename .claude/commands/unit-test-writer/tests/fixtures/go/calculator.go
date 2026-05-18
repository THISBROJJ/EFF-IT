package calculator

import "errors"

func Add(a, b float64) float64 {
	return a + b
}

func Subtract(a, b float64) float64 {
	return a - b
}

func Multiply(a, b float64) float64 {
	return a * b
}

func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("division by zero")
	}
	return a / b, nil
}

func Power(base float64, exp int) (float64, error) {
	if exp < 0 {
		return 0, errors.New("negative exponents not supported")
	}
	result := 1.0
	for range exp {
		result *= base
	}
	return result, nil
}
