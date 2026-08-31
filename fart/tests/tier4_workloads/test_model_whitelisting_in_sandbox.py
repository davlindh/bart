"""Tier 4 Workload Tests: ML & Model Whitelisting inside Local Sandbox (Requirement R3)."""

import pytest
from antigravity.sandbox import ASTSecurityValidator, LocalSandbox, SecurityViolationError


class TestMLSecurityWhitelisting:
    """Test AST security validation and execution of ML packages and models."""

    def test_ml_module_imports_allowed(self):
        validator = ASTSecurityValidator()
        safe_ml_codes = [
            "import torch",
            "import torch.nn as nn",
            "from transformers import AutoModelForCausalLM, AutoTokenizer",
            "import tokenizers",
            "import safetensors",
            "import onnxruntime",
            "import accelerate",
            "from antigravity.models import LocalModelRunner, NemotronEngine",
        ]
        for code in safe_ml_codes:
            validator.validate(code)  # Should not raise SecurityViolationError

    def test_model_modules_attribute_false_positive_remediated(self):
        validator = ASTSecurityValidator()
        code = """
class MockModel:
    def modules(self):
        return ["layer1", "layer2"]

m = MockModel()
for mod in m.modules():
    pass
"""
        # Validates that 'modules' is no longer blocked as a prohibited attribute
        validator.validate(code)

    def test_prohibited_modules_and_dunders_remain_blocked(self):
        validator = ASTSecurityValidator()
        malicious_codes = [
            "import os; os.system('echo pwned')",
            "import sys; sys.exit(0)",
            "import subprocess; subprocess.run(['ls'])",
            "().__class__.__subclasses__()",
            "getattr(obj, '__globals__')",
        ]
        for code in malicious_codes:
            with pytest.raises((SecurityViolationError, Exception)):
                validator.validate(code)

    def test_local_model_execution_inside_sandbox(self):
        sb = LocalSandbox(sandbox_id="sb-test-ml-models")
        try:
            code = """
from antigravity.models import LocalModelRunner, ModelConfig

runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
result = runner.generate("Quantum physics is", max_new_tokens=5)
print(f"OUTPUT_TOKENS={result.tokens_generated}")
"""
            res = sb.execute(code)
            assert res.exit_code == 0
            assert "OUTPUT_TOKENS=" in res.stdout
        finally:
            sb.destroy()

    def test_tensor_dunder_operators_inside_sandbox(self):
        sb = LocalSandbox(sandbox_id="sb-test-tensor-ops")
        try:
            code = """
class Matrix:
    def __init__(self, data):
        self.data = data
    def __matmul__(self, other):
        return Matrix([[sum(a * b for a, b in zip(r, c)) for c in zip(*other.data)] for r in self.data])

m1 = Matrix([[1, 2], [3, 4]])
m2 = Matrix([[5, 6], [7, 8]])
m3 = m1 @ m2
print(f"RESULT={m3.data[0][0]}")
"""
            res = sb.execute(code)
            assert res.exit_code == 0
            assert "RESULT=19" in res.stdout
        finally:
            sb.destroy()
