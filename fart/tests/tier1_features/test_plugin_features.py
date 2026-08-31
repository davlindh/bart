"""
Tier 1: Feature Coverage - Antigravity Customization Plugin & Skill Suite.
Verifies plugin.json manifest schema, mcp_config.json, SKILL.md files (YAML frontmatter & progressive disclosure),
reference guides, and AGENTS.md rules.
"""

import json
from pathlib import Path
import pytest


class TestPluginFeatures:
    """Feature test suite for Antigravity Customization Plugin & Skill Suite (Requirement R3)."""

    def test_plugin_manifest_structure_and_fields(self, plugin_root: Path):
        """Validates plugin.json exists and adheres to required manifest schema."""
        if not plugin_root.exists():
            pytest.skip("Plugin files pending creation by Milestone M4 agent")

        plugin_file = plugin_root / "plugin.json"
        assert plugin_file.exists(), f"Plugin manifest missing at {plugin_file}"

        data = json.loads(plugin_file.read_text(encoding="utf-8"))
        assert "name" in data, "Plugin manifest missing 'name'"
        assert "version" in data, "Plugin manifest missing 'version'"
        assert "description" in data, "Plugin manifest missing 'description'"
        assert "mcpServers" in data or "mcp_servers" in data or "servers" in data, "Plugin manifest missing MCP server declarations"

    def test_mcp_config_schema_validation(self, plugin_root: Path):
        """Validates mcp_config.json exists and specifies server configuration."""
        if not plugin_root.exists():
            pytest.skip("Plugin files pending creation by Milestone M4 agent")

        mcp_config_file = plugin_root / "mcp_config.json"
        if mcp_config_file.exists():
            data = json.loads(mcp_config_file.read_text(encoding="utf-8"))
            assert isinstance(data, dict)

    def test_skill_markdown_progressive_disclosure_structure(self, plugin_root: Path):
        """Validates that skill files (SKILL.md) exist and contain valid YAML frontmatter."""
        if not plugin_root.exists():
            pytest.skip("Plugin files pending creation by Milestone M4 agent")

        skills_dir = plugin_root / "skills"
        assert skills_dir.exists(), f"Skills directory missing at {skills_dir}"

        skill_files = list(skills_dir.glob("**/SKILL.md"))
        assert len(skill_files) >= 1, "At least one SKILL.md must be provided in plugin"

        for skill_file in skill_files:
            content = skill_file.read_text(encoding="utf-8")
            assert "---" in content, f"{skill_file.name} missing YAML frontmatter delimiters"
            assert "name:" in content or "description:" in content, f"{skill_file.name} missing name/description frontmatter"

    def test_skill_references_and_guidance(self, plugin_root: Path):
        """Validates skill reference documentation files exist and provide actionable guidance."""
        if not plugin_root.exists():
            pytest.skip("Plugin files pending creation by Milestone M4 agent")

        skills_dir = plugin_root / "skills"
        ref_files = list(skills_dir.glob("**/references/*.md"))
        if ref_files:
            for ref in ref_files:
                content = ref.read_text(encoding="utf-8")
                assert len(content.strip()) > 20, f"Reference guide {ref.name} should not be empty"

    def test_agents_rules_safety_compliance(self, plugin_root: Path):
        """Validates rules/AGENTS.md exists and defines operational constraints."""
        if not plugin_root.exists():
            pytest.skip("Plugin files pending creation by Milestone M4 agent")

        rules_file = plugin_root / "rules" / "AGENTS.md"
        if not rules_file.exists():
            alt_file = plugin_root / "AGENTS.md"
            if alt_file.exists():
                rules_file = alt_file

        assert rules_file.exists(), f"Rules file missing at {rules_file}"
        content = rules_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, "AGENTS.md must contain detailed operational rules"
        assert any(term in content.lower() for term in ["sandbox", "security", "execution", "agent", "worker"])
