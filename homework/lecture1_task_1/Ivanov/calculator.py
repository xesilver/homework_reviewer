# Task 1: Basic Calculator
# Student: Ivanov

def add(a, b):
    """
    Add two numbers.
    
    Args:
        a (float): First number
        b (float): Second number
        
    Returns:
        float: Sum of a and b
    """
    return a + b

def subtract(a, b):
    """
    Subtract second number from first.
    
    Args:
        a (float): First number
        b (float): Second number
        
    Returns:
        float: Difference of a and b
    """
    return a - b

def multiply(a, b):
    """
    Multiply two numbers.
    
    Args:
        a (float): First number
        b (float): Second number
        
    Returns:
        float: Product of a and b
    """
    return a * b

def divide(a, b):
    """
    Divide first number by second.
    
    Args:
        a (float): First number
        b (float): Second number
        
    Returns:
        float: Quotient of a and b
        
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def main():
    """Main function to demonstrate calculator operations."""
    print("Simple Calculator")
    print("Operations: +, -, *, /")
    
    try:
        num1 = float(input("Enter first number: "))
        operation = input("Enter operation (+, -, *, /): ")
        num2 = float(input("Enter second number: "))
        
        if operation == '+':
            result = add(num1, num2)
        elif operation == '-':
            result = subtract(num1, num2)
        elif operation == '*':
            result = multiply(num1, num2)
        elif operation == '/':
            result = divide(num1, num2)
        else:
            print("Invalid operation")
            return
        
        print(f"Result: {result}")
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
