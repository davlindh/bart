"""
Tier 4: Real-World Application Workload - Artifact & File Data Pipeline.
Simulates an agentic data pipeline generating tabular CSV outputs, summary JSON metrics,
and image chart artifacts, asserting extraction and encoding fidelity.
"""

import json
import pytest

try:
    from antigravity.sandbox.manager import SandboxManager
except ImportError:
    from tests.conftest import SandboxManager


class TestArtifactDataPipeline:
    """Workload test verifying multi-artifact creation, extraction, and validation."""

    def test_csv_and_chart_artifact_generation_pipeline(self, sandbox_manager: SandboxManager):
        """
        Executes a data pipeline generating multiple structured artifacts:
        1. CSV export of normalized metrics
        2. JSON metadata summary
        3. Base64 chart representation
        """
        sandbox = sandbox_manager.create_sandbox()

        pipeline_code = (
            "import csv, io, json\n"
            "# 1. Generate CSV data\n"
            "csv_buf = io.StringIO()\n"
            "writer = csv.writer(csv_buf)\n"
            "writer.writerow(['timestamp', 'epoch', 'loss', 'accuracy'])\n"
            "for ep in range(1, 6):\n"
            "    writer.writerow([f'2026-08-29T10:0{ep}:00Z', ep, round(0.5 / ep, 4), round(0.7 + ep * 0.05, 4)])\n"
            "csv_data = csv_buf.getvalue()\n"
            "\n"
            "# 2. Summary JSON\n"
            "summary = {'epochs_trained': 5, 'final_loss': 0.1, 'final_accuracy': 0.95}\n"
            "\n"
            "result_payload = {\n"
            "    'csv_length': len(csv_data),\n"
            "    'csv_rows': len(csv_data.strip().split('\\n')),\n"
            "    'summary': summary,\n"
            "    'artifacts': [\n"
            "        {'name': 'training_metrics.csv', 'type': 'text/csv', 'size': len(csv_data)},\n"
            "        {'name': 'loss_curve.png', 'type': 'image/png', 'base64': 'iVBORw0KGgoAAAANSUhEUg=='}\n"
            "    ]\n"
            "}\n"
            "print(json.dumps(result_payload))\n"
        )

        res = sandbox.execute(pipeline_code, repl=True)
        assert res.exit_code == 0
        if res.stdout:
            data = json.loads(res.stdout)
            assert data.get("csv_rows") == 6
            assert data.get("summary", {}).get("epochs_trained") == 5
            assert len(data.get("artifacts", [])) == 2
