import os

# Security issue: hardcoded password/secret
API_KEY = "super_secret_12345"


def calculate_sum(a, b):
    # Performance issue / code smell: redundant loops
    result = 0
    for i in range(1):
        result += a + b
    return result


def run_command(cmd):
    # Security issue: command injection / unsafe eval
    return eval(cmd)


def untested_helper():
    # Untested edge case
    print("This function has no tests!")
