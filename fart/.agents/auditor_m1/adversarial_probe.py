"""
Adversarial Security Probe for Milestone 1 Sandbox Subsystem.
Stress-tests dynamic evasion techniques, runtime builtins tampering, and resource exhaustion.
"""

from pathlib import Path
import sys
import time

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from antigravity.sandbox import LocalSandbox, SecurityViolationError


def run_adversarial_probes():
    print("==================================================")
    print("Starting Adversarial Probes for Milestone 1")
    print("==================================================")

    sandbox = LocalSandbox(timeout=5.0)

    # 1. Dynamic chr() based attribute construction
    print("\n--- Probe 1: Dynamic string-constructed dunder access via getattr ---")
    attack_1 = "getattr(int, chr(95)*2 + 'subclasses' + chr(95)*2)()"
    res_1 = sandbox.execute(attack_1)
    assert not res_1.is_success, f"Attack 1 succeeded unexpectedly: {res_1.stdout}"
    assert "SecurityViolationError" in str(res_1.error) or "SecurityViolationError" in res_1.stderr
    print("  [BLOCKED] Dynamic getattr with chr() was blocked by runtime safe_getattr hook.")

    # 2. Dynamic __globals__ access via lambda func
    print("\n--- Probe 2: Dynamic __globals__ access via runtime safe_getattr ---")
    attack_2 = "f = lambda: 1\ngetattr(f, chr(95)*2 + 'globals' + chr(95)*2)"
    res_2 = sandbox.execute(attack_2)
    assert not res_2.is_success
    assert "SecurityViolationError" in str(res_2.error) or "SecurityViolationError" in res_2.stderr
    print("  [BLOCKED] Dynamic globals attribute access blocked.")

    # 3. Dynamic __import__ of forbidden modules
    print("\n--- Probe 3: Dynamic __import__('os') at runtime ---")
    attack_3 = "__import__(chr(111) + chr(115))"
    res_3 = sandbox.execute(attack_3)
    assert not res_3.is_success
    assert "SecurityViolationError" in str(res_3.error) or "SecurityViolationError" in res_3.stderr
    print("  [BLOCKED] Runtime __import__ of 'os' blocked by create_safe_importer.")

    # 4. Attempting to overwrite sanitized builtins
    print("\n--- Probe 4: Attempting to poison __builtins__ dictionary ---")
    attack_4 = "__builtins__['open'] = lambda *a, **k: 'poisoned'\n'open' in __builtins__"
    res_4 = sandbox.execute(attack_4)
    # Even if they add a lambda into their session dict, it cannot access OS primitives
    # because real open was never passed to the worker
    assert res_4.is_success
    # Try calling real OS methods
    res_4b = sandbox.execute("import os")
    assert not res_4b.is_success
    print("  [SECURE] Builtins poisoning cannot restore stripped C-level OS functions.")

    # 5. Exception handling and memory limit under rapid allocation
    print("\n--- Probe 5: Memory exhaustion attempt (allocation within safety limit) ---")
    attack_5 = "big_list = [0] * (5 * 1024 * 1024)\nlen(big_list)"
    res_5 = sandbox.execute(attack_5)
    assert res_5.is_success
    assert res_5.result == "5242880"
    print("  [PASS] Safe large allocation handled cleanly.")

    # 6. Deep recursion handling
    print("\n--- Probe 6: Deep recursion handling ---")
    attack_6 = "def recurse(n):\n    return recurse(n + 1)\nrecurse(0)"
    res_6 = sandbox.execute(attack_6)
    assert not res_6.is_success
    assert "RecursionError" in res_6.stderr or "RecursionError" in str(res_6.error)
    print("  [PASS] RecursionError caught without sandbox process crash.")

    sandbox.terminate()
    print("\n==================================================")
    print("ADVERSARIAL ASSESSMENT: ALL PROBES PROPERLY DEFENDED")
    print("==================================================")


if __name__ == "__main__":
    run_adversarial_probes()
