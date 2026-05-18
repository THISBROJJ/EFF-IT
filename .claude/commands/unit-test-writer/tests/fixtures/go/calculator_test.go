// Intentionally incomplete — covers only Add and Subtract.
// unit-test-writer should detect Multiply, Divide, and Power are untested
// and generate tests to bring coverage to ≥90%.

package calculator

import "testing"

func TestAdd(t *testing.T) {
	result := Add(2, 3)
	if result != 5 {
		t.Errorf("Add(2, 3) = %v, want 5", result)
	}
}

func TestSubtract(t *testing.T) {
	result := Subtract(10, 4)
	if result != 6 {
		t.Errorf("Subtract(10, 4) = %v, want 6", result)
	}
}
