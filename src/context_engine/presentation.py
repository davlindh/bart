"""Multi-Tier Presentation Formatter (Human L1, Human L2, Machine JSON, Navigation View)."""

import json
from typing import Any, Dict
from src.core.contracts import ContextPacket


class PresentationFormatter:
    """Formats ContextPackets into multi-tier user and machine representations."""

    @classmethod
    def format_human_l1_summary(cls, packet: ContextPacket) -> str:
        """Human Level 1: Concise executive digest."""
        node_labels = [n.label for n in packet.nodes]
        evidence_summary = (
            f" Identified {len(packet.evidence)} empirical evidence items."
            if packet.evidence
            else ""
        )
        return (
            f"### Context Summary ({packet.role})\n"
            f"**Focal Point:** `{packet.target_node}` | **Task:** {packet.task}\n\n"
            f"Resolved **{len(packet.nodes)}** key entities ({', '.join(node_labels[:3])}). "
            f"Current operational scope is `{packet.scope.depth.value}` with {len(packet.relations)} active dependencies."
            f"{evidence_summary}"
        )

    @classmethod
    def format_human_l2_detailed(cls, packet: ContextPacket) -> str:
        """Human Level 2: In-depth operational view with evidence citations."""
        lines = [
            f"## Detailed Context Brief: {packet.target_node}",
            f"- **Role / Persona:** {packet.role}",
            f"- **Operational Purpose:** {packet.purpose}",
            f"- **Specific Task:** {packet.task}",
            f"- **Scope Boundaries:** Depth `{packet.scope.depth.value}`, Allowed Domains: `{[d.value for d in packet.scope.allowed_domains]}`",
            "",
            "### Bounded Entities & Scores",
        ]
        for node in packet.nodes:
            lines.append(f"- **{node.label}** (`{node.id}`) | Domain: `{node.domain.value}` | Relevance: `{node.relevance_score}`")
            if node.properties:
                for k, v in node.properties.items():
                    lines.append(f"  • *{k}*: {v}")

        if packet.relations:
            lines.append("\n### Active Relationships & Dependencies")
            for rel in packet.relations:
                lines.append(f"- `{rel.source}` --[{rel.type} (conf: {rel.confidence})]--> `{rel.target}`")

        if packet.evidence:
            lines.append("\n### Empirical Evidence")
            for ev in packet.evidence:
                lines.append(f"- [{ev.source_ref}] {ev.fact} *(confidence: {ev.confidence})*")

        if packet.assumptions:
            lines.append("\n### Assumptions")
            for asm in packet.assumptions:
                lines.append(f"- {asm}")

        if packet.uncertainties:
            lines.append("\n### Uncertainties")
            for unc in packet.uncertainties:
                lines.append(f"- ⚠️ {unc}")

        return "\n".join(lines)

    @classmethod
    def format_machine_json(cls, packet: ContextPacket, indent: int = 2) -> str:
        """Machine Structured View: Full JSON schema payload."""
        return packet.model_dump_json(indent=indent)

    @classmethod
    def format_navigation_view(cls, packet: ContextPacket) -> str:
        """Navigation View: Next recommended exploration nodes."""
        lines = [
            f"### Next Exploration Points for `{packet.target_node}`",
            "Adjacent nodes ranked by progressive relevance:",
            "",
        ]
        if not packet.recommended_next_nodes:
            lines.append("- *No adjacent nodes found outside current scope boundary.*")
        else:
            for idx, rec in enumerate(packet.recommended_next_nodes, start=1):
                rationale_str = f" — *{rec.rationale}*" if rec.rationale else ""
                lines.append(f"{idx}. **{rec.label}** (`{rec.node_id}`) — Relevance: **{rec.relevance}**{rationale_str}")

        lines.append(f"\n*Scope Expansion Available:* `D1 -> D2` if further context required.")
        return "\n".join(lines)
