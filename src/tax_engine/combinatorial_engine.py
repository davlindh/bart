"""Combinatorial Tax Engine: Optimizes, bundles, and resolves conflicts across Swedish tax cuts."""

from typing import List, Dict, Any, Optional
from itertools import combinations
from ..core.types import TaxRuleType
from ..core.contracts import TaxOptimizationOpportunity
from .models import (
    TaxTransaction,
    TaxStrategyBundle,
    CombinationEvaluation,
)
from .rule_library import (
    VMBRule,
    RUTRule,
    ROTRule,
    GronTeknikRule,
    ReverseChargeConstructionRule,
    MinorAssetWriteOffRule,
    PeriodiseringsfondRule,
    K10DividendRule,
    FoUDeductionRule,
)


class CombinatorialTaxEngine:
    """Evaluates cross-regime tax cuts, resolves structural conflicts, and synthesizes maximum-potency strategy bundles."""

    # Explicit conflict matrix (Rules that cannot co-exist on the same line item/transaction)
    MUTUAL_EXCLUSIONS = {
        (TaxRuleType.RUT_DEDUCTION, TaxRuleType.ROT_DEDUCTION): "Samma arbetskostnad kan inte erhålla både RUT (50%) och ROT (30%) enligt IL 67 kap.",
        (TaxRuleType.VMB_MARGIN_TAX, TaxRuleType.STANDARD_MOMS_25): "En vara kan inte samtidigt säljas med full 25% moms och VMB marginalmoms.",
        (TaxRuleType.REVERSE_CHARGE_CONSTRUCTION, TaxRuleType.STANDARD_MOMS_25): "Byggtjänst till byggföretag får inte faktureras med utgående moms.",
    }

    # Synergistic rule pairs (where combining generates extra economic multiplier or cash efficiency)
    SYNERGY_MULTIPLIERS = {
        frozenset([TaxRuleType.VMB_MARGIN_TAX, TaxRuleType.RUT_DEDUCTION]): {
            "name": "Begagnat Inbyte + Nyckelfärdig RUT-Installation",
            "synergy_pct": 0.05,  # 5% extra margin retention via customer lock-in
            "description": "Kunden byter in begagnad maskin (VMB sparar moms) och köper ny installation med 50% RUT-avdrag."
        },
        frozenset([TaxRuleType.GRON_TEKNIK, TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET]): {
            "name": "Grön Omställning + Direktavskrivning av Installationsverktyg",
            "synergy_pct": 0.04,
            "description": "50% skattereduktion på batteri/laddbox kombineras med 100% omedelbar kostnadsföring av mätinstrument."
        },
        frozenset([TaxRuleType.PERIODISERINGSFOND, TaxRuleType.K10_DIVIDEND_OPTIMAL]): {
            "name": "Optimal Ägar- och Bolagsskatteallokering",
            "synergy_pct": 0.08,
            "description": "25% vinstskatt skjuts upp i 6 år via P-fond medan ägarutdelning maximeras till 20% skatt via K10 löneunderlag."
        },
    }

    @classmethod
    def analyze_combinatorial_opportunities(
        cls,
        transactions: List[TaxTransaction],
        annual_taxable_profit: Optional[float] = None,
        total_salaries_paid: Optional[float] = None,
        owner_salary: Optional[float] = None,
        monthly_rd_salaries: Optional[float] = None,
    ) -> CombinationEvaluation:
        """Runs the combinatorial optimizer over transactions and company-level financials."""
        individual_opportunities: List[TaxOptimizationOpportunity] = []
        conflicts: List[str] = []
        synergies: List[str] = []

        # 1. Evaluate Transaction-level Tax Cuts
        for tx in transactions:
            vmb = VMBRule.evaluate(tx)
            if vmb: individual_opportunities.append(vmb[0])

            rut = RUTRule.evaluate(tx)
            if rut: individual_opportunities.append(rut[0])

            rot = ROTRule.evaluate(tx)
            if rot: individual_opportunities.append(rot[0])

            gron = GronTeknikRule.evaluate(tx)
            if gron: individual_opportunities.append(gron[0])

            rev = ReverseChargeConstructionRule.evaluate(tx)
            if rev: individual_opportunities.append(rev)

            asset = MinorAssetWriteOffRule.evaluate(tx)
            if asset: individual_opportunities.append(asset[0])

        # 2. Evaluate Company-Level Financial Tax Cuts
        if annual_taxable_profit and annual_taxable_profit > 10000.0:
            pfond = PeriodiseringsfondRule.evaluate_company_profit(annual_taxable_profit)
            if pfond: individual_opportunities.append(pfond[0])

        if total_salaries_paid and total_salaries_paid > 0 and owner_salary:
            k10 = K10DividendRule.evaluate_dividend_space(total_salaries_paid, owner_salary)
            if k10: individual_opportunities.append(k10[0])

        if monthly_rd_salaries and monthly_rd_salaries > 20000.0:
            fou = FoUDeductionRule.evaluate_rd_team(monthly_rd_salaries)
            if fou: individual_opportunities.append(fou[0])

        # 3. Detect Conflicts Across Opportunities
        tx_rules_map: Dict[str, List[TaxOptimizationOpportunity]] = {}
        for opp in individual_opportunities:
            tx_rules_map.setdefault(opp.transaction_id, []).append(opp)

        valid_opportunities: List[TaxOptimizationOpportunity] = []
        for tx_id, opps in tx_rules_map.items():
            if len(opps) == 1:
                valid_opportunities.append(opps[0])
            else:
                # Multiple opportunities on the same transaction -> resolve conflict by highest net profit delta
                opp_types = [o.best_possible_rule for o in opps]
                for (r1, r2), reason in cls.MUTUAL_EXCLUSIONS.items():
                    if r1 in opp_types and r2 in opp_types:
                        conflicts.append(f"Konflikt på {tx_id}: {reason}")
                
                # Pick the highest economic value option
                best_opp = max(opps, key=lambda o: (o.net_profit_delta_sek + o.net_tax_saved_sek))
                valid_opportunities.append(best_opp)

        # 4. Detect Cross-Strategy Synergies & Construct Optimal Strategy Bundles
        active_rules = set(o.best_possible_rule for o in valid_opportunities)
        total_synergy_bonus = 0.0

        for rule_pair, syn_data in cls.SYNERGY_MULTIPLIERS.items():
            if rule_pair.issubset(active_rules):
                matched_opps = [o for o in valid_opportunities if o.best_possible_rule in rule_pair]
                base_sum = sum(o.net_profit_delta_sek + o.net_tax_saved_sek for o in matched_opps)
                bonus = round(base_sum * syn_data["synergy_pct"], 2)
                total_synergy_bonus += bonus
                synergies.append(f"Synergi upptäckt: '{syn_data['name']}' (+{bonus:.0f} SEK mervärde)")

        # 5. Synthesize Curated Strategy Bundles
        bundles: List[TaxStrategyBundle] = []

        # Bundle A: Operational & Transactional Quick Wins (Moms & Avdrag)
        trans_opps = [o for o in valid_opportunities if o.transaction_id not in ("ANNUAL_PROFIT", "K10_DIVIDEND", "MONTHLY_PAYROLL")]
        if trans_opps:
            tot_tax = sum(o.net_tax_saved_sek for o in trans_opps)
            tot_cash = sum(o.net_profit_delta_sek for o in trans_opps)
            bundles.append(
                TaxStrategyBundle(
                    bundle_id="BUNDLE_MOMS_FLOW",
                    name="Operativ Moms- & Likviditetsoptimering (Transaktionsflöde)",
                    description="Omedelbara skattevinster via VMB, RUT/ROT, Grön teknik och direktavskrivning i det dagliga kassaflödet.",
                    included_rule_types=list(set(o.best_possible_rule for o in trans_opps)),
                    opportunities=trans_opps,
                    total_tax_saved_sek=tot_tax,
                    total_cash_retention_sek=tot_cash,
                    synergy_bonus_sek=round(total_synergy_bonus * 0.4, 2),
                    net_economic_benefit_sek=tot_tax + tot_cash + round(total_synergy_bonus * 0.4, 2),
                    risk_level="LOW",
                    legal_references=list(set(o.legal_basis for o in trans_opps)),
                    prerequisites=[
                        "Underlag för inköpspris på inbytta maskiner (kvitto privatperson).",
                        "Personnummer och fastighetsbeteckning för RUT-kunder.",
                        "Verifiering av F-skatt på byggkunder.",
                    ],
                )
            )

        # Bundle B: High-Leverage Strategic & Owner Wealth Bundle (P-fond, FoU, K10)
        strat_opps = [o for o in valid_opportunities if o.transaction_id in ("ANNUAL_PROFIT", "K10_DIVIDEND", "MONTHLY_PAYROLL")]
        if strat_opps:
            tot_tax = sum(o.net_tax_saved_sek for o in strat_opps)
            tot_cash = sum(o.net_profit_delta_sek for o in strat_opps)
            bundles.append(
                TaxStrategyBundle(
                    bundle_id="BUNDLE_STRATEGIC_WEALTH",
                    name="Strategisk Bolags- & Ägarbeskattning (Bokslut & K10)",
                    description="Skjuter upp bolagsskatt, minskar arbetsgivaravgifter och maximerar utdelning till 20% kapitalskatt.",
                    included_rule_types=list(set(o.best_possible_rule for o in strat_opps)),
                    opportunities=strat_opps,
                    total_tax_saved_sek=tot_tax,
                    total_cash_retention_sek=tot_cash,
                    synergy_bonus_sek=round(total_synergy_bonus * 0.6, 2),
                    net_economic_benefit_sek=tot_tax + tot_cash + round(total_synergy_bonus * 0.6, 2),
                    risk_level="LOW",
                    legal_references=list(set(o.legal_basis for o in strat_opps)),
                    prerequisites=[
                        "Bokslutsdisposition i årsredovisning (Periodiseringsfond).",
                        "Dokumenterade FoU-arbetstimmar i tidsredovisning.",
                        "K10 underlag bifogat till privat Inkomstdeklaration 1.",
                    ],
                )
            )

        # Total combined savings across all conflict-free opportunities
        max_savings = sum(o.net_tax_saved_sek + o.net_profit_delta_sek for o in valid_opportunities) + total_synergy_bonus

        return CombinationEvaluation(
            evaluated_strategies_count=len(individual_opportunities),
            optimal_bundles=bundles,
            detected_conflicts=conflicts,
            synergy_opportunities=synergies,
            max_combined_savings_sek=round(max_savings, 2),
        )
