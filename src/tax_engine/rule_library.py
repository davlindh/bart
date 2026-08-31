"""Swedish Tax Cut & Optimization Rule Library: Formal rule catalog with statutory grounding, triggers, and tax savings formulas."""

from typing import Dict, Any, List, Optional, Tuple
from ..core.types import TaxRuleType
from ..core.contracts import TaxOptimizationOpportunity
from .models import (
    TaxTransaction,
    CustomerTaxProfile,
    VMBCalculation,
    RUTCalculation,
    ROTCalculation,
    GronTeknikCalculation,
    PeriodiseringsfondCalculation,
    K10Calculation,
    FoUCalculation,
    AssetDepreciationEvaluation,
)


class TaxCutRule:
    """Base class for a modular Swedish tax cut rule."""
    rule_type: TaxRuleType
    title: str
    category: str  # 'VAT_MOMS', 'CORPORATE_TAX_INKOMSTSKATT', 'SOCIAL_FEES_ARBETSGIVARAVGIFTER', 'OWNER_TAX_3_12'
    legal_basis: str
    recommended_account: str
    description: str

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, Any]]:
        raise NotImplementedError


class VMBRule(TaxCutRule):
    """Vinstmarginalbeskattning (ML 9a kap.) — 20% tax on gross margin for second-hand trade-ins."""
    rule_type = TaxRuleType.VMB_MARGIN_TAX
    title = "VMB Marginalbeskattning (ML 9a kap.)"
    category = "VAT_MOMS"
    legal_basis = "Mervärdesskattelagen (1994:200 / 2023:200) 9a kap."
    recommended_account = "3051 Försäljning varor VMB"

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, VMBCalculation]]:
        if not tx.is_used_good or not tx.bought_from_private_individual:
            return None

        sales_price_gross = tx.gross_amount
        purchase_cost = tx.purchase_cost_ex_vat
        gross_margin = sales_price_gross - purchase_cost

        if gross_margin <= 0:
            return None

        standard_vat = round(sales_price_gross - (sales_price_gross / 1.25), 2)
        standard_profit = round((sales_price_gross / 1.25) - purchase_cost, 2)
        vmb_vat = round(gross_margin * 0.20, 2)
        vmb_profit = round(sales_price_gross - vmb_vat - purchase_cost, 2)
        vat_saved = round(standard_vat - vmb_vat, 2)
        profit_gain = round(vmb_profit - standard_profit, 2)
        profit_pct = round((profit_gain / standard_profit) * 100.0, 1) if standard_profit > 0 else 100.0

        calc = VMBCalculation(
            sales_price_gross=sales_price_gross,
            purchase_cost=purchase_cost,
            gross_margin=gross_margin,
            standard_vat_amount=standard_vat,
            standard_profit_after_vat=standard_profit,
            vmb_profit_margin=gross_margin,
            vmb_vat_amount=vmb_vat,
            vmb_profit_after_vat=vmb_profit,
            vat_saved_sek=vat_saved,
            profit_increase_sek=profit_gain,
            profit_increase_pct=profit_pct,
        )

        if tx.current_tax_rule == TaxRuleType.STANDARD_MOMS_25 and vat_saved > 0:
            opp = TaxOptimizationOpportunity(
                opportunity_id=f"vmb_opp_{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                applied_rule=TaxRuleType.STANDARD_MOMS_25,
                best_possible_rule=TaxRuleType.VMB_MARGIN_TAX,
                applied_tax_sek=standard_vat,
                best_possible_tax_sek=vmb_vat,
                net_tax_saved_sek=vat_saved,
                net_profit_delta_sek=profit_gain,
                legal_basis=cls.legal_basis,
                recommended_bas_account=cls.recommended_account,
                moms_box_change="Fält 05/10 -> Fält 08/10",
                explanation=f"VMB tillämpas på inbyte köpt av privatperson. Beskattar endast marginalen ({gross_margin:.0f} SEK), sparar {vat_saved:.2f} SEK i moms.",
            )
            return opp, calc
        return None


class RUTRule(TaxCutRule):
    """RUT-avdrag (IL 67 kap.) — 50% skattereduktion på arbetskostnad för trädgård/robotinstallation."""
    rule_type = TaxRuleType.RUT_DEDUCTION
    title = "RUT-avdrag 50% Arbetskostnad (IL 67 kap.)"
    category = "VAT_MOMS"
    legal_basis = "Inkomstskattelagen (1999:1229) 67 kap."
    recommended_account = "3002 Försäljning arbetskostnad RUT"

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, RUTCalculation]]:
        if not tx.is_garden_or_installation_work and not tx.is_labor_service:
            return None
        if tx.customer and tx.customer.is_company:
            return None

        total_gross = tx.gross_amount
        labor_gross = tx.labor_share_amount if tx.labor_share_amount > 0 else (total_gross * 0.35)
        material_gross = total_gross - labor_gross
        rut_deduction = round(labor_gross * 0.50, 2)
        customer_payable = round(total_gross - rut_deduction, 2)
        customer_saving_pct = round((rut_deduction / total_gross) * 100.0, 1)

        calc = RUTCalculation(
            total_package_gross=total_gross,
            material_cost_gross=material_gross,
            labor_cost_gross=labor_gross,
            standard_customer_payable=total_gross,
            standard_company_revenue=total_gross,
            rut_deduction_amount=rut_deduction,
            rut_customer_payable=customer_payable,
            skatteverket_payout_amount=rut_deduction,
            total_company_revenue_with_rut=total_gross,
            customer_saving_sek=rut_deduction,
            customer_saving_pct=customer_saving_pct,
        )

        if tx.current_tax_rule != TaxRuleType.RUT_DEDUCTION and rut_deduction > 0:
            opp = TaxOptimizationOpportunity(
                opportunity_id=f"rut_opp_{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                applied_rule=tx.current_tax_rule,
                best_possible_rule=TaxRuleType.RUT_DEDUCTION,
                applied_tax_sek=round(total_gross - (total_gross / 1.25), 2),
                best_possible_tax_sek=round(total_gross - (total_gross / 1.25), 2),
                net_tax_saved_sek=0.0,
                net_profit_delta_sek=rut_deduction,
                legal_basis=cls.legal_basis,
                recommended_bas_account=cls.recommended_account,
                moms_box_change="Fält 05 & 10 (Full moms, 50% arbetskostnad rekvireras från Skatteverket)",
                explanation=f"Installation för privatkund. Kunden sparar {rut_deduction:.0f} SEK (50% av arbetet), företaget behåller 100% intäkt.",
            )
            return opp, calc
        return None


class ROTRule(TaxCutRule):
    """ROT-avdrag (IL 67 kap.) — 30% skattereduktion på reparation och ombyggnad av bostad."""
    rule_type = TaxRuleType.ROT_DEDUCTION
    title = "ROT-avdrag 30% Arbetskostnad (IL 67 kap.)"
    category = "VAT_MOMS"
    legal_basis = "Inkomstskattelagen 67 kap. 9 § (Reparation, underhåll, om- och tillbyggnad)"
    recommended_account = "3003 Försäljning arbetskostnad ROT"

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, ROTCalculation]]:
        # Triggers when transaction is marked as building/repair labor for a private individual
        is_rot_candidate = (
            "reparation" in tx.description.lower() or "renovering" in tx.description.lower() or "ombyggnad" in tx.description.lower()
        )
        if not is_rot_candidate or (tx.customer and tx.customer.is_company):
            return None

        total_gross = tx.gross_amount
        labor_gross = tx.labor_share_amount if tx.labor_share_amount > 0 else (total_gross * 0.50)
        material_gross = total_gross - labor_gross
        rot_deduction = round(labor_gross * 0.30, 2)
        customer_payable = round(total_gross - rot_deduction, 2)

        calc = ROTCalculation(
            total_package_gross=total_gross,
            material_cost_gross=material_gross,
            labor_cost_gross=labor_gross,
            standard_customer_payable=total_gross,
            standard_company_revenue=total_gross,
            rot_deduction_amount=rot_deduction,
            rot_customer_payable=customer_payable,
            skatteverket_payout_amount=rot_deduction,
            total_company_revenue_with_rot=total_gross,
            customer_saving_sek=rot_deduction,
            customer_saving_pct=round((rot_deduction / total_gross) * 100.0, 1),
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id=f"rot_opp_{tx.transaction_id}",
            transaction_id=tx.transaction_id,
            applied_rule=tx.current_tax_rule,
            best_possible_rule=TaxRuleType.ROT_DEDUCTION,
            applied_tax_sek=round(total_gross - (total_gross / 1.25), 2),
            best_possible_tax_sek=round(total_gross - (total_gross / 1.25), 2),
            net_tax_saved_sek=0.0,
            net_profit_delta_sek=rot_deduction,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="Fält 05 & 10 (Full moms, 30% arbetskostnad rekvireras från Skatteverket)",
            explanation=f"Bygg-/reparationsarbete för privatperson berättigar till 30% ROT-avdrag på arbetskostnaden ({labor_gross:.0f} SEK).",
        )
        return opp, calc


class GronTeknikRule(TaxCutRule):
    """Grön Teknik (IL 67 kap. 38-44 §§) — 50% avdrag på batterilagring och laddbox, 20% på solceller."""
    rule_type = TaxRuleType.GRON_TEKNIK
    title = "Grön Teknik Skattereduktion (IL 67 kap.)"
    category = "VAT_MOMS"
    legal_basis = "Inkomstskattelagen (1999:1229) 67 kap. 38-44 §§ & Lag (2020:1066)"
    recommended_account = "3004 Försäljning Grön Teknik"

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, GronTeknikCalculation]]:
        desc_lower = tx.description.lower()
        is_battery = "batteri" in desc_lower or "energilagring" in desc_lower or "solcellsbatteri" in desc_lower
        is_charging = "laddbox" in desc_lower or "laddstation" in desc_lower or "laddare" in desc_lower
        is_solar = "solcell" in desc_lower or "solpaneler" in desc_lower

        if not (is_battery or is_charging or is_solar) or (tx.customer and tx.customer.is_company):
            return None

        install_type = "BATTERY_STORAGE" if is_battery else ("EV_CHARGING" if is_charging else "SOLAR_PANELS")
        rate = 0.50 if install_type in ("BATTERY_STORAGE", "EV_CHARGING") else 0.20
        deduction = round(tx.gross_amount * rate, 2)
        customer_pay = round(tx.gross_amount - deduction, 2)

        calc = GronTeknikCalculation(
            installation_type=install_type,
            total_gross=tx.gross_amount,
            deduction_rate=rate,
            deduction_amount=deduction,
            customer_payable=customer_pay,
            skatteverket_claim=deduction,
            customer_saving_sek=deduction,
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id=f"gron_opp_{tx.transaction_id}",
            transaction_id=tx.transaction_id,
            applied_rule=tx.current_tax_rule,
            best_possible_rule=TaxRuleType.GRON_TEKNIK,
            applied_tax_sek=round(tx.gross_amount - (tx.gross_amount / 1.25), 2),
            best_possible_tax_sek=round(tx.gross_amount - (tx.gross_amount / 1.25), 2),
            net_tax_saved_sek=0.0,
            net_profit_delta_sek=deduction,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="Fält 05 & 10 (Grön teknik faktura med direktavdrag på totalbeloppet)",
            explanation=f"Grön teknik ({install_type}): Privatkund får {rate*100:.0f}% skattereduktion direkt på fakturan ({deduction:.0f} SEK avdrag).",
        )
        return opp, calc


class ReverseChargeConstructionRule(TaxCutRule):
    """Omvänd byggmoms (ML 1 kap. 2 § första stycket 4 b)."""
    rule_type = TaxRuleType.REVERSE_CHARGE_CONSTRUCTION
    title = "Omvänd Byggmoms (ML 1 kap. 2 §)"
    category = "VAT_MOMS"
    legal_basis = "Mervärdesskattelagen 1 kap. 2 § första stycket 4 b"
    recommended_account = "3231 Försäljning omvänd byggmoms"

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[TaxOptimizationOpportunity]:
        if not tx.is_garden_or_installation_work:
            return None
        cust = tx.customer
        if not cust or not cust.is_company or not cust.has_f_skatt:
            return None

        is_construction = False
        if cust.sni_code:
            clean = cust.sni_code.replace(".", "").strip()
            if clean.startswith(("41", "42", "43")):
                is_construction = True

        if is_construction and tx.current_tax_rule == TaxRuleType.STANDARD_MOMS_25:
            vat = tx.current_vat_amount
            return TaxOptimizationOpportunity(
                opportunity_id=f"rev_charge_opp_{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                applied_rule=TaxRuleType.STANDARD_MOMS_25,
                best_possible_rule=TaxRuleType.REVERSE_CHARGE_CONSTRUCTION,
                applied_tax_sek=vat,
                best_possible_tax_sek=0.0,
                net_tax_saved_sek=vat,
                net_profit_delta_sek=0.0,
                legal_basis=cls.legal_basis,
                recommended_bas_account=cls.recommended_account,
                moms_box_change="Fält 05/10 -> Fält 41",
                explanation=f"Köparen ({cust.name}, SNI {cust.sni_code}) är byggföretag. Fakturera utan moms till fält 41.",
            )
        return None


class MinorAssetWriteOffRule(TaxCutRule):
    """Direktavskrivning av inventarier av mindre värde (< 1/2 PBB, IL 18 kap. 4 §)."""
    rule_type = TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET
    title = "Direktavskrivning av inventarier < 1/2 PBB (IL 18 kap. 4 §)"
    category = "CORPORATE_TAX_INKOMSTSKATT"
    legal_basis = "Inkomstskattelagen (1999:1229) 18 kap. 4 §"
    recommended_account = "5410 Förbrukningsinventarier"

    DEFAULT_PBB_HALF = 28650.0

    @classmethod
    def evaluate(cls, tx: TaxTransaction, **kwargs) -> Optional[Tuple[TaxOptimizationOpportunity, AssetDepreciationEvaluation]]:
        if not tx.is_asset_purchase:
            return None

        pbb_half = kwargs.get("pbb_half", cls.DEFAULT_PBB_HALF)
        cost_ex_vat = tx.net_amount
        qualifies = cost_ex_vat <= pbb_half

        if not qualifies or tx.current_tax_rule == TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET:
            return None

        tax_direct = round(cost_ex_vat * 0.206, 2)
        tax_deprec = round((cost_ex_vat / 5.0) * 0.206, 2)
        cash_advantage = round(tax_direct - tax_deprec, 2)

        eval_model = AssetDepreciationEvaluation(
            purchase_price_ex_vat=cost_ex_vat,
            half_prisbasbelopp_threshold=pbb_half,
            qualifies_for_direct_write_off=True,
            year_1_deduction_direct=cost_ex_vat,
            year_1_deduction_depreciation=cost_ex_vat / 5.0,
            year_1_tax_saving_direct=tax_direct,
            year_1_tax_saving_depreciation=tax_deprec,
            immediate_cash_retention_advantage=cash_advantage,
            recommended_account=cls.recommended_account,
            recommended_treatment="Direktavskrivning år 1 (100% kostnadsfört)",
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id=f"asset_write_off_{tx.transaction_id}",
            transaction_id=tx.transaction_id,
            applied_rule=tx.current_tax_rule,
            best_possible_rule=TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET,
            applied_tax_sek=tax_deprec,
            best_possible_tax_sek=tax_direct,
            net_tax_saved_sek=cash_advantage,
            net_profit_delta_sek=cash_advantage,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="N/A (Bokförs i resultaträkningen)",
            explanation=f"Inköp av utrustning ({cost_ex_vat:.0f} SEK ex moms) < 1/2 PBB. Direktavdrag ger {cash_advantage:.2f} SEK direkt likviditetsfördel.",
        )
        return opp, eval_model


class PeriodiseringsfondRule(TaxCutRule):
    """Periodiseringsfond (IL 30 kap.) — uppskjutning av upp till 25% av skattepliktig vinst i 6 år."""
    rule_type = TaxRuleType.PERIODISERINGSFOND
    title = "Periodiseringsfond 25% (IL 30 kap.)"
    category = "CORPORATE_TAX_INKOMSTSKATT"
    legal_basis = "Inkomstskattelagen (1999:1229) 30 kap."
    recommended_account = "8811 Avsättning till periodiseringsfond / 2110 Periodiseringsfonder"

    @classmethod
    def evaluate_company_profit(cls, taxable_profit_sek: float) -> Optional[Tuple[TaxOptimizationOpportunity, PeriodiseringsfondCalculation]]:
        if taxable_profit_sek <= 10000.0:
            return None

        max_alloc = round(taxable_profit_sek * 0.25, 2)
        tax_deferral = round(max_alloc * 0.206, 2)

        calc = PeriodiseringsfondCalculation(
            taxable_profit_before_allocation=taxable_profit_sek,
            max_allocation_rate=0.25,
            max_allocation_amount=max_alloc,
            corporate_tax_rate=0.206,
            tax_deferral_benefit_sek=tax_deferral,
            max_deferral_years=6,
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id="p_fond_annual_allocation",
            transaction_id="ANNUAL_PROFIT",
            applied_rule=TaxRuleType.TAX_EXEMPT,
            best_possible_rule=TaxRuleType.PERIODISERINGSFOND,
            applied_tax_sek=round(taxable_profit_sek * 0.206, 2),
            best_possible_tax_sek=round((taxable_profit_sek - max_alloc) * 0.206, 2),
            net_tax_saved_sek=tax_deferral,
            net_profit_delta_sek=tax_deferral,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="N/A (Bokslutsdisposition i INK2)",
            explanation=f"Avsättning av 25% av vinsten ({max_alloc:.0f} SEK) skjuter upp {tax_deferral:.0f} SEK i bolagsskatt i upp till 6 år (räntefritt rörelsekapital).",
        )
        return opp, calc


class K10DividendRule(TaxCutRule):
    """3:12 K10 Utdelningsoptimering (IL 57 kap.) — Schablon vs Lönebaserat utrymme för 20% skatt."""
    rule_type = TaxRuleType.K10_DIVIDEND_OPTIMAL
    title = "K10 3:12 Utdelningsoptimering (IL 57 kap.)"
    category = "OWNER_TAX_3_12"
    legal_basis = "Inkomstskattelagen (1999:1229) 57 kap. (Gränsbelopp & Löneunderlag)"
    recommended_account = "K10 Blankett / Eget kapital"

    FORENKLINGSBELOPP_2025 = 209550.0

    @classmethod
    def evaluate_dividend_space(
        cls, total_salaries_paid: float, owner_salary: float, fiscal_year: int = 2025
    ) -> Tuple[TaxOptimizationOpportunity, K10Calculation]:
        schablon = cls.FORENKLINGSBELOPP_2025
        # Qualification for wage-based rule: owner must take out min salary: 6 IBB + 5% of total or 9.6 IBB
        min_salary_req = min(500000.0, 400000.0 + total_salaries_paid * 0.05)
        qualifies_wage = owner_salary >= min_salary_req and total_salaries_paid > 0

        wage_space = round(total_salaries_paid * 0.50, 2) if qualifies_wage else 0.0
        use_wage = qualifies_wage and wage_space > schablon

        optimal_rule = "LONEBASERAT" if use_wage else "SCHABLON"
        optimal_gransbelopp = wage_space if use_wage else schablon
        tax_at_20 = round(optimal_gransbelopp * 0.20, 2)
        # Benefit compared to taking as salary with ~52% marginal tax + 31.42% social fees
        salary_tax_equivalent = round(optimal_gransbelopp * 0.50, 2)
        tax_saved = round(salary_tax_equivalent - tax_at_20, 2)

        calc = K10Calculation(
            fiscal_year=fiscal_year,
            forenklingsbelopp=schablon,
            total_qualifying_wages=total_salaries_paid,
            owner_wage=owner_salary,
            qualifies_for_wage_rule=qualifies_wage,
            wage_based_space=wage_space,
            optimal_rule=optimal_rule,
            optimal_gransbelopp=optimal_gransbelopp,
            tax_at_20_pct=tax_at_20,
            comparison_vs_salary_tax_saving=tax_saved,
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id="k10_optimal_dividend_space",
            transaction_id="K10_DIVIDEND",
            applied_rule=TaxRuleType.TAX_EXEMPT,
            best_possible_rule=TaxRuleType.K10_DIVIDEND_OPTIMAL,
            applied_tax_sek=salary_tax_equivalent,
            best_possible_tax_sek=tax_at_20,
            net_tax_saved_sek=tax_saved,
            net_profit_delta_sek=tax_saved,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="N/A (K10 underlag i privat Inkomstdeklaration 1)",
            explanation=(
                f"Optimal K10 strategi ({optimal_rule}): Gränsbelopp {optimal_gransbelopp:.0f} SEK kan tas ut "
                f"till endast 20% kapitalskatt ({tax_at_20:.0f} SEK skatt), vilket sparar {tax_saved:.0f} SEK "
                f"jämfört med lönebeskattning."
            ),
        )
        return opp, calc


class FoUDeductionRule(TaxCutRule):
    """Forsknings- och utvecklingsavdrag (FoU) — Nedsättning av arbetsgivaravgifter med 10% + 10% skatteavdrag."""
    rule_type = TaxRuleType.FOU_DEDUCTION
    title = "FoU-avdrag Arbetsgivaravgifter (Socialavgiftslagen)"
    category = "SOCIAL_FEES_ARBETSGIVARAVGIFTER"
    legal_basis = "Lag (2013:948) om stöd till forskning och utveckling"
    recommended_account = "7510 Arbetsgivaravgifter (Reducerade)"

    @classmethod
    def evaluate_rd_team(cls, rd_gross_monthly_salaries: float, rd_hours_pct: float = 1.0) -> Optional[Tuple[TaxOptimizationOpportunity, FoUCalculation]]:
        if rd_gross_monthly_salaries <= 20000.0 or rd_hours_pct < 0.50:
            return None

        # 10 percentage points reduction on employer contributions (up to cap)
        monthly_saving = round(rd_gross_monthly_salaries * 0.1959, 2)  # 10% reduction + 9.59% base deduction
        annual_saving = round(monthly_saving * 12.0, 2)

        calc = FoUCalculation(
            rd_staff_hours=rd_hours_pct * 160.0,
            rd_gross_salaries=rd_gross_monthly_salaries,
            standard_social_fees=round(rd_gross_monthly_salaries * 0.3142, 2),
            reduced_social_fees=round(rd_gross_monthly_salaries * (0.3142 - 0.1959), 2),
            monthly_saving_sek=monthly_saving,
            annual_saving_sek=annual_saving,
        )

        opp = TaxOptimizationOpportunity(
            opportunity_id="fou_social_fees_reduction",
            transaction_id="MONTHLY_PAYROLL",
            applied_rule=TaxRuleType.TAX_EXEMPT,
            best_possible_rule=TaxRuleType.FOU_DEDUCTION,
            applied_tax_sek=round(rd_gross_monthly_salaries * 0.3142 * 12, 2),
            best_possible_tax_sek=round(rd_gross_monthly_salaries * (0.3142 - 0.1959) * 12, 2),
            net_tax_saved_sek=annual_saving,
            net_profit_delta_sek=annual_saving,
            legal_basis=cls.legal_basis,
            recommended_bas_account=cls.recommended_account,
            moms_box_change="N/A (Arbetsgivardeklaration AGI fält 056)",
            explanation=f"FoU-avdrag på utvecklingspersonal sparar {monthly_saving:.0f} SEK/mån ({annual_saving:.0f} SEK/år) i arbetsgivaravgifter.",
        )
        return opp, calc


# Master Rule Registry
ALL_TAX_RULES = [
    VMBRule,
    RUTRule,
    ROTRule,
    GronTeknikRule,
    ReverseChargeConstructionRule,
    MinorAssetWriteOffRule,
    PeriodiseringsfondRule,
    K10DividendRule,
    FoUDeductionRule,
]
