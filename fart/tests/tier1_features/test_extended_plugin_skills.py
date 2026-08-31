"""
Tier 1: Feature Coverage - Extended Plugin Skills & AGENTS.md Directives (Requirement R4).
Verifies skills/local-inference and skills/disk-persistence SKILL.md and all references.
"""

import json
from pathlib import Path
import pytest


class TestExtendedPluginSkills:
    """Test suite verifying local-inference and disk-persistence skills and AGENTS.md rules."""

    def test_local_inference_skill_and_references(self, plugin_root: Path):
        """Validates local-inference SKILL.md and its 4 reference markdown documents."""
        skill_dir = plugin_root / "skills" / "local-inference"
        assert skill_dir.exists(), f"Missing {skill_dir}"

        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "name: local-inference" in content
        assert "load_model" in content
        assert "model_generate" in content
        assert "model_chat" in content

        ref_dir = skill_dir / "references"
        assert ref_dir.exists()
        expected_refs = [
            "nemotron-architecture.md",
            "device-and-precision.md",
            "chat-templates.md",
            "generation-parameters.md",
        ]
        for ref_name in expected_refs:
            ref_file = ref_dir / ref_name
            assert ref_file.exists(), f"Missing reference {ref_name}"
            ref_content = ref_file.read_text(encoding="utf-8")
            assert len(ref_content.strip()) > 50

    def test_disk_persistence_skill_and_references(self, plugin_root: Path):
        """Validates disk-persistence SKILL.md and its 3 reference markdown documents."""
        skill_dir = plugin_root / "skills" / "disk-persistence"
        assert skill_dir.exists(), f"Missing {skill_dir}"

        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "name: disk-persistence" in content
        assert "persist_sandbox" in content
        assert "restore_sandbox_disk" in content
        assert "list_persisted_sandboxes" in content

        ref_dir = skill_dir / "references"
        assert ref_dir.exists()
        expected_refs = [
            "session-persistence.md",
            "snapshot-branching.md",
            "worker-recovery.md",
        ]
        for ref_name in expected_refs:
            ref_file = ref_dir / ref_name
            assert ref_file.exists(), f"Missing reference {ref_name}"
            ref_content = ref_file.read_text(encoding="utf-8")
            assert len(ref_content.strip()) > 50

    def test_plugin_manifest_skills_catalog(self, plugin_root: Path):
        """Validates plugin.json references all 5 skills."""
        plugin_file = plugin_root / "plugin.json"
        data = json.loads(plugin_file.read_text(encoding="utf-8"))
        skills = data.get("skills", [])
        assert "skills/local-inference" in skills
        assert "skills/disk-persistence" in skills
        assert "skills/sandbox-execution" in skills
        assert "skills/worker-orchestration" in skills
        assert "skills/snapshot-management" in skills

    def test_agents_rules_extended_sections(self, plugin_root: Path):
        """Validates AGENTS.md includes sections 9 and 10."""
        rules_file = plugin_root / "rules" / "AGENTS.md"
        content = rules_file.read_text(encoding="utf-8")
        assert "9. Local Model Inference Directives" in content
        assert "10. Disk Persistence & Session Durability Directives" in content
        assert "Nemotron" in content
        assert "WAL" in content
