# Task 1: Basic Calculator
# Student: Petrov

def calc(a, b, op):
    """Calculate result based on operation."""
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            return "Error: Division by zero"
        return a / b
    else:
        return "Invalid operation"

# Main program
print("Calculator")
num1 = float(input("First number: "))
op = input("Operation: ")
num2 = float(input("Second number: "))
result = calc(num1, num2, op)
print(f"Result: {result}")
