import asyncio
import os
import shutil
import tempfile
import time
from typing import Dict, List, Tuple
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

import config
from schemas import ReviewResult, Finding
from agents.specialists import ReviewDeps, read_file
from review import review_pr_async
from tests.eval_cases import EVAL_CASES, EvalCase

# Setup Anthropic Model
if config.ANTHROPIC_API_KEY:
    model = AnthropicModel("claude-3-5-sonnet-latest")
else:
    model = "anthropic:claude-3-5-sonnet-latest"

# Single Agent definition (fair comparison - has access to read_file tool)
single_agent = Agent(
    model,
    deps_type=ReviewDeps,
    output_type=ReviewResult,
    system_prompt=(
        "You are an expert code reviewer. Review the given git diff to identify security "
        "vulnerabilities, code quality issues, and testing issues.\n"
        "For each issue found, emit a Finding containing the file name, line number, "
        "severity ('critical', 'warning', 'info'), category ('security', 'quality', or 'tests'), "
        "and a descriptive message.\n"
        "If you need more file context, use the `read_file` tool to inspect the contents of any file."
    ),
    tools=[read_file],
)


def get_agent_output(result) -> ReviewResult:
    """Safely extracts output from Agent run result supporting different pydantic-ai versions."""
    if hasattr(result, "output"):
        return result.output
    if hasattr(result, "data"):
        return result.data
    return result


async def run_single_agent_review(diff: str, local_repo_path: str) -> List[Finding]:
    """Runs the single-agent pipeline."""
    deps = ReviewDeps(
        mcp_session=None,
        local_repo_path=local_repo_path,
        owner="mock_owner",
        repo="mock_repo",
    )
    result = await single_agent.run(
        f"Review this git diff:\n{diff}",
        deps=deps,
    )
    extracted = get_agent_output(result)
    return extracted.findings if hasattr(extracted, "findings") else []


async def run_multi_agent_review(diff: str, local_repo_path: str) -> List[Finding]:
    """Runs the multi-agent pipeline (Orchestrator -> Specialists -> Verifier)."""
    # Using the review_pr_async from review.py with post_to_github=False
    # Since we are running offline, we must wrap it and extract the raw list of findings.
    # To get the raw findings instead of the markdown text, we can temporarily inspect the flow,
    # or we can mock/run the steps of review_pr_async directly.
    # Let's run the steps directly to get the actual Finding objects!
    from agents.orchestrator import route_specialists
    from agents.specialists import review_security, review_quality, review_tests
    from agents.verifier import verify_findings

    selected_specialists = route_specialists(diff)
    if not selected_specialists:
        return []

    deps = ReviewDeps(
        mcp_session=None,
        local_repo_path=local_repo_path,
        owner="mock_owner",
        repo="mock_repo",
    )

    tasks = []
    if "security" in selected_specialists:
        tasks.append(review_security(diff, deps))
    if "quality" in selected_specialists:
        tasks.append(review_quality(diff, deps))
    if "tests" in selected_specialists:
        tasks.append(review_tests(diff, deps))

    results = await asyncio.gather(*tasks)

    all_findings = []
    for res in results:
        findings_list = res.findings if hasattr(res, "findings") else []
        all_findings.extend(findings_list)

    verified_result = await verify_findings(diff, all_findings, deps)
    return verified_result.findings if hasattr(verified_result, "findings") else []


def setup_mock_repo(mock_files: Dict[str, str]) -> str:
    """Creates a temp directory with mock repository files."""
    temp_dir = tempfile.mkdtemp()
    for rel_path, content in mock_files.items():
        full_path = os.path.join(temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    return temp_dir


def teardown_mock_repo(temp_dir: str):
    """Cleans up the temp directory."""
    shutil.rmtree(temp_dir)


def calculate_metrics(
    predicted: List[Finding], expected: List[Finding]
) -> Tuple[int, int, int, float, float, float]:
    """Calculates True Positives, False Positives, False Negatives, Precision, Recall, and F1-Score."""
    tp = 0
    fp = 0
    matched_expected = set()

    for pred in predicted:
        matched = False
        for i, exp in enumerate(expected):
            if i in matched_expected:
                continue
            # Match condition: same file, same category, line within 2 lines
            line_match = (pred.line is None and exp.line is None) or (
                pred.line is not None
                and exp.line is not None
                and abs(pred.line - exp.line) <= 2
            )
            if (
                pred.file.lower() == exp.file.lower()
                and pred.category.lower() == exp.category.lower()
                and line_match
            ):
                tp += 1
                matched_expected.add(i)
                matched = True
                break
        if not matched:
            fp += 1

    fn = len(expected) - len(matched_expected)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return tp, fp, fn, precision, recall, f1


async def evaluate():
    print("=" * 60)
    print("      PR REVIEW AGENT EVALUATION RUNNER")
    print("=" * 60)

    results_md = [
        "# PR Review Agent Evaluation Report",
        "",
        f"Evaluation run date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Performance Comparison",
        "",
        "| Metric | Single-Agent | Multi-Agent |",
        "| :--- | :--- | :--- |",
    ]

    total_single_tp, total_single_fp, total_single_fn = 0, 0, 0
    total_multi_tp, total_multi_fp, total_multi_fn = 0, 0, 0

    single_total_time = 0.0
    multi_total_time = 0.0

    for case in EVAL_CASES:
        print(f"\nEvaluating: {case.name}...")
        temp_dir = setup_mock_repo(case.mock_files)

        try:
            # 1. Run Single-Agent
            print("  Running Single-Agent...")
            t0 = time.time()
            single_findings = await run_single_agent_review(case.diff, temp_dir)
            t_single = time.time() - t0
            single_total_time += t_single

            # 2. Run Multi-Agent
            print("  Running Multi-Agent...")
            t0 = time.time()
            multi_findings = await run_multi_agent_review(case.diff, temp_dir)
            t_multi = time.time() - t0
            multi_total_time += t_multi

            # Calculate metrics
            s_tp, s_fp, s_fn, s_prec, s_rec, s_f1 = calculate_metrics(
                single_findings, case.expected_findings
            )
            m_tp, m_fp, m_fn, m_prec, m_rec, m_f1 = calculate_metrics(
                multi_findings, case.expected_findings
            )

            total_single_tp += s_tp
            total_single_fp += s_fp
            total_single_fn += s_fn

            total_multi_tp += m_tp
            total_multi_fp += m_fp
            total_multi_fn += m_fn

            # Print Case summary
            print(f"    Single-Agent -> TP: {s_tp}, FP: {s_fp}, FN: {s_fn} | F1: {s_f1:.2f} | Latency: {t_single:.2f}s")
            print(f"    Multi-Agent  -> TP: {m_tp}, FP: {m_fp}, FN: {m_fn} | F1: {m_f1:.2f} | Latency: {t_multi:.2f}s")

        finally:
            teardown_mock_repo(temp_dir)

    # Compute aggregate metrics
    s_precision = total_single_tp / (total_single_tp + total_single_fp) if (total_single_tp + total_single_fp) > 0 else 0.0
    s_recall = total_single_tp / (total_single_tp + total_single_fn) if (total_single_tp + total_single_fn) > 0 else 0.0
    s_f1_total = 2 * s_precision * s_recall / (s_precision + s_recall) if (s_precision + s_recall) > 0 else 0.0

    m_precision = total_multi_tp / (total_multi_tp + total_multi_fp) if (total_multi_tp + total_multi_fp) > 0 else 0.0
    m_recall = total_multi_tp / (total_multi_tp + total_multi_fn) if (total_multi_tp + total_multi_fn) > 0 else 0.0
    m_f1_total = 2 * m_precision * m_recall / (m_precision + m_recall) if (m_precision + m_recall) > 0 else 0.0

    # Add to markdown report list
    results_md.append(f"| **True Positives (TP)** | {total_single_tp} | {total_multi_tp} |")
    results_md.append(f"| **False Positives (FP)** | {total_single_fp} | {total_multi_fp} |")
    results_md.append(f"| **False Negatives (FN)** | {total_single_fn} | {total_multi_fn} |")
    results_md.append(f"| **Precision** | {s_precision:.2%} | {m_precision:.2%} |")
    results_md.append(f"| **Recall** | {s_recall:.2%} | {m_recall:.2%} |")
    results_md.append(f"| **F1-Score** | {s_f1_total:.2%} | {m_f1_total:.2%} |")
    results_md.append(f"| **Total Latency** | {single_total_time:.2f}s | {multi_total_time:.2f}s |")

    report_str = "\n".join(results_md)

    # Write report to evaluation_results.md
    with open("evaluation_results.md", "w", encoding="utf-8") as f:
        f.write(report_str)

    print("\n" + "=" * 60)
    print("             EVALUATION REPORT SUMMARY")
    print("=" * 60)
    print(f"Single-Agent Precision: {s_precision:.2%}, Recall: {s_recall:.2%}, F1: {s_f1_total:.2%}")
    print(f"Multi-Agent  Precision: {m_precision:.2%}, Recall: {m_recall:.2%}, F1: {m_f1_total:.2%}")
    print(f"Single-Agent Time: {single_total_time:.2f}s | Multi-Agent Time: {multi_total_time:.2f}s")
    print("=" * 60)
    print("Detailed report saved to evaluation_results.md")


if __name__ == "__main__":
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY.startswith("your-"):
        print("Warning: ANTHROPIC_API_KEY in .env is missing or a placeholder. Running evaluations will fail.")
    asyncio.run(evaluate())
