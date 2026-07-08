from dataclasses import dataclass
from typing import Dict, List
from schemas import Finding


@dataclass
class EvalCase:
    name: str
    diff: str
    mock_files: Dict[str, str]  # file_path -> content
    expected_findings: List[Finding]


EVAL_CASES: List[EvalCase] = [
    EvalCase(
        name="Case 1: Security Vulnerabilities",
        diff=(
            "diff --git a/auth.py b/auth.py\n"
            "new file mode 100644\n"
            "index 0000000..e69de29\n"
            "--- /dev/null\n"
            "+++ b/auth.py\n"
            "@@ -0,0 +1,11 @@\n"
            "+import os\n"
            "+\n"
            '+API_KEY = "super_secret_token_abc123"\n'
            "+\n"
            "+def authenticate(user):\n"
            "+    print(f'Authenticating user {user}')\n"
            "+\n"
            "+def execute_user_command(user_input):\n"
            "+    os.system(user_input)\n"
        ),
        mock_files={
            "auth.py": (
                "import os\n"
                "\n"
                'API_KEY = "super_secret_token_abc123"\n'
                "\n"
                "def authenticate(user):\n"
                "    print(f'Authenticating user {user}')\n"
                "\n"
                "def execute_user_command(user_input):\n"
                "    os.system(user_input)\n"
            )
        },
        expected_findings=[
            Finding(
                file="auth.py",
                line=3,
                severity="critical",
                category="security",
                message="Hardcoded API key or credentials.",
            ),
            Finding(
                file="auth.py",
                line=9,
                severity="critical",
                category="security",
                message="Unsafe os.system execution allowing command injection.",
            ),
        ],
    ),
    EvalCase(
        name="Case 2: Quality Issues & Code Smell",
        diff=(
            "diff --git a/utils.py b/utils.py\n"
            "new file mode 100644\n"
            "index 0000000..e69de29\n"
            "--- /dev/null\n"
            "+++ b/utils.py\n"
            "@@ -0,0 +1,8 @@\n"
            "+def find_duplicates(items):\n"
            "+    duplicates = []\n"
            "+    for i in range(len(items)):\n"
            "+        for j in range(len(items)):\n"
            "+            if i != j and items[i] == items[j] and items[i] not in duplicates:\n"
            "+                duplicates.append(items[i])\n"
            "+    return duplicates\n"
        ),
        mock_files={
            "utils.py": (
                "def find_duplicates(items):\n"
                "    duplicates = []\n"
                "    for i in range(len(items)):\n"
                "        for j in range(len(items)):\n"
                "            if i != j and items[i] == items[j] and items[i] not in duplicates:\n"
                "                duplicates.append(items[i])\n"
                "    return duplicates\n"
            )
        },
        expected_findings=[
            Finding(
                file="utils.py",
                line=1,
                severity="warning",
                category="quality",
                message="O(N^2) duplicate search is inefficient. Use a set for O(N) complexity.",
            )
        ],
    ),
    EvalCase(
        name="Case 3: Inadequate Test Coverage",
        diff=(
            "diff --git a/payment.py b/payment.py\n"
            "new file mode 100644\n"
            "index 0000000..e69de29\n"
            "--- /dev/null\n"
            "+++ b/payment.py\n"
            "@@ -0,0 +1,6 @@\n"
            "+def process_payment(amount, token):\n"
            "+    if amount <= 0:\n"
            '+        raise ValueError("Amount must be positive")\n'
            "+    print(f'Processing payment of {amount}')\n"
            "+    return True\n"
        ),
        mock_files={
            "payment.py": (
                "def process_payment(amount, token):\n"
                "    if amount <= 0:\n"
                '        raise ValueError("Amount must be positive")\n'
                "    print(f'Processing payment of {amount}')\n"
                "    return True\n"
            )
        },
        expected_findings=[
            Finding(
                file="payment.py",
                line=1,
                severity="warning",
                category="tests",
                message="Missing unit tests for the process_payment function.",
            )
        ],
    ),
]
