# Task 1: Basic Calculator
# Student: Sidorov

# Calculator functions
def add(x, y):
    return x + y

def sub(x, y):
    return x - y

def mul(x, y):
    return x * y

def div(x, y):
    return x / y

# Get user input
a = float(input("Enter first number: "))
b = float(input("Enter second number: "))
op = input("Enter operation (+, -, *, /): ")

# Calculate and display result
if op == '+':
    print(add(a, b))
elif op == '-':
    print(sub(a, b))
elif op == '*':
    print(mul(a, b))
elif op == '/':
    if b != 0:
        print(div(a, b))
    else:
        print("Cannot divide by zero")
else:
    print("Invalid operation")
