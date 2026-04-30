# test_cases.py

TEST_CASES = [
    {
        "name": "Valid arithmetic and print",
        "source": """
x = 10
y = 20
z = x + y
print(z)
"""
    },
    {
        "name": "Syntax error missing expression",
        "source": """
a = 5
b =
print(a + b)
"""
    },
    {
        "name": "Valid conditional",
        "source": """
x = 3
if x > 0:
    print("positive")
else:
    print("non-positive")
"""
    }
]