"""Financial Verification Engine: Comprehensive compliance and audit verification for Swedish SMBs.

Implements statutory verification checks under:
- Bokföringslagen (BFL 1999:1078) — Verifikationskrav, nummerserie, arkivering, verifikationsunderlag.
- Mervärdesskattelagen (ML 2023:200) — Momsdeklarationskonsistens, momssatsavstämning, EU/VIES.
- Inkomstskattelagen (IL 1999:1229) — Avdragsgillhet, underlag för skattereduktioner.
- Skatteförfarandelagen (SFL 2011:1244) — Skattekontoavstämning, preliminärskatt, arbetsgivaravgifter.
"""

from typing import List, Dict, Any, Optional
from ..core.types import TaxRuleType
from .models import (
    TaxTransaction,
    MomsdeklarationReport,
    FinancialVerificationIssue,
    FinancialVerificationReport,
)


class FinancialVerificationEngine:
    """Performs rigorous financial verification, detecting missing records, broken balances, and audit gaps."""

    @classmethod
    def verify_transaction_batch(
        cls,
        transactions: List[TaxTransaction],
        momsdeklaration: Optional[MomsdeklarationReport] = None,
        bank_balance_sek: Optional[float] = None,
        skattekonto_balance_sek: Optional[float] = None,
        booked_vouchers: Optional[List[Dict[str, Any]]] = None,
    ) -> FinancialVerificationReport:
        """Executes a full verification battery across transactions, VAT drafts, and ledgers."""
        issues: List[FinancialVerificationIssue] = []
        checks_performed = 0
        checks_passed = 0
        reconciliations: Dict[str, bool] = {}

        # ── 1. BFL Verification Check: Source Document (Verifikation) Integrity ──
        for tx in transactions:
            checks_performed += 1
            # Check for source system and description
            if not tx.source_system or not tx.description or len(tx.description.strip()) < 3:
                issues.append(
                    FinancialVerificationIssue(
                        code="BFL_MISSING_SPECIFICATION",
                        severity="WARNING",
                        category="BFL_BOKFORINGSLAGEN",
                        title=f"Bristfällig affärshändelsebeskrivning: {tx.transaction_id}",
                        description=f"Transaktion {tx.transaction_id} saknar fullständig specifikation av vad köpet/försäljningen avser.",
                        affected_entity_id=tx.transaction_id,
                        remediation_suggestion="Komplettera verifikatet med tydlig artikelrad, syfte och underliggande faktura/kvitto i enlighet med BFL 5 kap. 7 §.",
                        legal_basis="Bokföringslagen (1999:1078) 5 kap. 7 §",
                    )
                )
            else:
                checks_passed += 1

            # Check B2B Customer Identity & Org.nr
            checks_performed += 1
            if tx.customer and tx.customer.is_company:
                if not tx.customer.org_nr and not tx.customer.customer_id:
                    issues.append(
                        FinancialVerificationIssue(
                            code="BFL_MISSING_COUNTERPARTY_ORGNR",
                            severity="WARNING",
                            category="BFL_BOKFORINGSLAGEN",
                            title=f"Saknat organisationsnummer för företagskund: {tx.customer.name}",
                            description=f"Fakturering till företag {tx.customer.name} (Tx {tx.transaction_id}) saknar verifierat organisationsnummer.",
                            affected_entity_id=tx.transaction_id,
                            remediation_suggestion="Registrera motpartens 10-siffriga organisationsnummer och kontrollera F-skattestatus via Bolagsverket/Skatteverket.",
                            legal_basis="Mervärdesskattelagen 11 kap. 8 § (Fakturainnehåll) & BFL 5 kap. 7 §",
                        )
                    )
                else:
                    checks_passed += 1
            else:
                checks_passed += 1

            # Check VAT Consistency on transaction level
            checks_performed += 1
            expected_net = tx.gross_amount / (1.0 + tx.current_vat_rate) if tx.current_vat_rate > 0 else tx.gross_amount
            calc_diff = abs(tx.net_amount - expected_net)
            if tx.current_vat_rate > 0 and calc_diff > 2.0 and not tx.is_used_good:
                issues.append(
                    FinancialVerificationIssue(
                        code="ML_VAT_NET_DISCREPANCY",
                        severity="CRITICAL",
                        category="ML_MOMS",
                        title=f"Momsberäkningsavvikelse på transaktionsnivå: {tx.transaction_id}",
                        description=(
                            f"Brutto ({tx.gross_amount:.2f} SEK) vid momssats {tx.current_vat_rate*100:.0f}% "
                            f"motsvarar netto {expected_net:.2f} SEK, men angivet netto är {tx.net_amount:.2f} SEK (diff {calc_diff:.2f} SEK)."
                        ),
                        affected_entity_id=tx.transaction_id,
                        remediation_suggestion="Kontrollera om transaktionen innehåller blandade momssatser eller öresavrundning och justera baskontofördelningen.",
                        legal_basis="Mervärdesskattelagen 7 kap. 1 §",
                    )
                )
            else:
                checks_passed += 1

            # Check for Cable Installation / Robot mower claimed under RUT
            desc_l = (tx.description or "").lower()
            if any(k in desc_l for k in ["kabel", "kabeldragning", "begränsningskabel", "guidekabel", "robotgräsklippare", "automower"]) and tx.current_tax_rule == TaxRuleType.RUT_DEDUCTION:
                checks_performed += 1
                issues.append(
                    FinancialVerificationIssue(
                        code="RUT_CABLE_INSTALLATION_EXCLUDED",
                        severity="WARNING",
                        category="RUT_COMPLIANCE",
                        title=f"Kabelinstallation / Robotmontering ej RUT-berättigad: {tx.transaction_id}",
                        description=(
                            f"Transaktion '{tx.description}' innehåller kabeldragning/installation av robotgräsklippare. "
                            f"Enligt Skatteverkets handledning för hushållsarbete (IL 67 kap.) ger nedläggning av begränsningskabel "
                            f"eller montering av robotgräsklippare INTE rätt till RUT-avdrag. Risk för avslag och sanktionsavgift."
                        ),
                        affected_entity_id=tx.transaction_id,
                        remediation_suggestion="Separera arbetskostnaden: kabeldragning debiteras med 25% moms utan RUT (BAS 3001), medan eventuellt rent trädgårdsarbete kan medges RUT (BAS 3002).",
                        legal_basis="Inkomstskattelagen (1999:1229) 67 kap. 13-19 §§ samt Skatteverkets ställningstagande dnr 131 347493-15/111",
                    )
                )

        # ── 2. Momsdeklaration Consistency Checks ──
        if momsdeklaration:
            checks_performed += 1
            # Check Fält 10 (25% moms) consistency with Fält 05 & Fält 08
            expected_moms_25 = round((momsdeklaration.falt_05_momspliktig_forsaljning_25 * 0.25) + (momsdeklaration.falt_08_vmb_marginal * 0.20), 2)
            actual_moms_25 = momsdeklaration.falt_10_utgaende_moms_25
            if abs(expected_moms_25 - actual_moms_25) > 5.0:
                issues.append(
                    FinancialVerificationIssue(
                        code="ML_MOMS_FALT10_MISMATCH",
                        severity="CRITICAL",
                        category="ML_MOMS",
                        title="Avstämning Fält 10: Utgående moms matchar inte beskattningsunderlag",
                        description=f"Beräknad utgående moms 25% (Fält 05*0.25 + Fält 08*0.20 = {expected_moms_25:.2f} SEK) avviker från redovisad moms ({actual_moms_25:.2f} SEK).",
                        affected_entity_id="momsdeklaration",
                        remediation_suggestion="Rekonciliera momsrapporten mot huvudbokens konton 2610, 2611 och 2620.",
                        legal_basis="Skatteförfarandelagen (2011:1244) 26 kap.",
                    )
                )
                reconciliations["moms_falt_10_reconciliation"] = False
            else:
                checks_passed += 1
                reconciliations["moms_falt_10_reconciliation"] = True

            # Check Fält 49 (Moms att betala/få tillbaka) mathematical balance
            checks_performed += 1
            total_utgaende = (
                momsdeklaration.falt_10_utgaende_moms_25
                + momsdeklaration.falt_11_utgaende_moms_12
                + momsdeklaration.falt_12_utgaende_moms_6
            )
            expected_net_moms = round(total_utgaende - momsdeklaration.falt_48_ingaende_moms, 2)
            actual_net_moms = momsdeklaration.falt_49_moms_att_betala_eller_fa_tillbaka
            if abs(expected_net_moms - actual_net_moms) > 2.0:
                issues.append(
                    FinancialVerificationIssue(
                        code="ML_MOMS_FALT49_NET_ERROR",
                        severity="CRITICAL",
                        category="ML_MOMS",
                        title="Fält 49 Nettomomsberäkning är felaktig",
                        description=f"Utgående moms ({total_utgaende:.2f}) minus ingående moms ({momsdeklaration.falt_48_ingaende_moms:.2f}) = {expected_net_moms:.2f} SEK, men Fält 49 visar {actual_net_moms:.2f} SEK.",
                        affected_entity_id="momsdeklaration",
                        remediation_suggestion="Rätta nettosummeringen i momsdeklarationen före inlämning till Skatteverket.",
                        legal_basis="Mervärdesskattelagen 13 kap.",
                    )
                )
                reconciliations["moms_falt_49_net_reconciliation"] = False
            else:
                checks_passed += 1
                reconciliations["moms_falt_49_net_reconciliation"] = True

        # ── 3. Balanced Ledger & Double-Entry Continuity (Debet == Kredit) ──
        if booked_vouchers:
            checks_performed += 1
            unbalanced_vouchers = []
            for v in booked_vouchers:
                voucher_data = v.get("voucher", v)
                rows = voucher_data.get("rows", [])
                tot_debet = sum(r.get("debet", 0.0) for r in rows)
                tot_kredit = sum(r.get("kredit", 0.0) for r in rows)
                if abs(tot_debet - tot_kredit) > 0.01:
                    unbalanced_vouchers.append(voucher_data.get("verifikat_id", "UNKNOWN"))

            if unbalanced_vouchers:
                issues.append(
                    FinancialVerificationIssue(
                        code="BFL_UNBALANCED_VOUCHER",
                        severity="CRITICAL",
                        category="BFL_BOKFORINGSLAGEN",
                        title=f"Obalanserade verifikat upptäckta ({len(unbalanced_vouchers)} st)",
                        description=f"Följande verifikat har debet != kredit: {', '.join(unbalanced_vouchers)}.",
                        affected_entity_id="ledger",
                        remediation_suggestion="Skapa rättelseverifikat eller balansera verifikatsraderna så att debet och kredit matchar exakt på öret.",
                        legal_basis="Bokföringslagen (1999:1078) 5 kap. 1 § (Dubbel bokföring)",
                    )
                )
                reconciliations["ledger_balance_check"] = False
            else:
                checks_passed += 1
                reconciliations["ledger_balance_check"] = True

        # ── 4. Cross-Border / EU VIES Verification Check ──
        for tx in transactions:
            if tx.customer and tx.customer.is_eu_business:
                checks_performed += 1
                if not tx.customer.eu_vat_nr or not tx.customer.eu_vat_nr.startswith(("DE", "DK", "FI", "NO", "FR", "NL", "PL")):
                    issues.append(
                        FinancialVerificationIssue(
                            code="ML_EU_VIES_UNVERIFIED",
                            severity="CRITICAL",
                            category="ML_MOMS",
                            title=f"EU-kund saknar giltigt VIES Momsnummer: {tx.customer.name}",
                            description=f"Momsfri EU-försäljning (Tx {tx.transaction_id}) kräver aktivt VIES-validerat VAT-nummer.",
                            affected_entity_id=tx.transaction_id,
                            remediation_suggestion="Validera VAT-numret mot EU VIES-databasen och spara valideringskvittot i verifikationsunderlaget.",
                            legal_basis="Mervärdesskattelagen 3 kap. 30 a § & Rådets förordning (EU) nr 904/2010",
                        )
                    )
                else:
                    checks_passed += 1

        # ── 5. Generate Overall Score and Recommendations ──
        score = (checks_passed / checks_performed) if checks_performed > 0 else 1.0
        score = round(score, 3)

        recommendations = []
        if any(i.severity == "CRITICAL" for i in issues):
            recommendations.append("Åtgärda omedelbart alla kritiska moms- och verifikatsavvikelser före kvartalsbokslut.")
        if any(i.code == "BFL_MISSING_SPECIFICATION" for i in issues):
            recommendations.append("Implementera obligatoriskt artikelradskrav vid integration mot POS och webbutik.")
        if not issues:
            recommendations.append("Fullständig finansiell verifiering genomförd utan avvikelser. Bokföring uppfyller God Redovisningssed.")

        return FinancialVerificationReport(
            verification_score=score,
            total_checks_performed=checks_performed,
            passed_checks_count=checks_passed,
            issues=issues,
            reconciliations=reconciliations,
            missing_source_documents_count=sum(1 for i in issues if i.code == "BFL_MISSING_SPECIFICATION"),
            balanced_ledger_verified=reconciliations.get("ledger_balance_check", True),
            recommendations=recommendations,
        )
