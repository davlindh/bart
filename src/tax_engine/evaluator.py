"""Core Tax Rule Evaluator comparing Applied vs Best Possible Swedish Tax Treatments."""

from typing import List, Optional, Tuple
from .models import (
    TaxTransaction,
    VMBCalculation,
    RUTCalculation,
    AssetDepreciationEvaluation,
)
from ..core.types import TaxRuleType
from ..core.contracts import TaxOptimizationOpportunity, TaxEvaluationResult


class TaxRuleEvaluator:
    """Evaluates applied tax treatments against legally compliant optimal alternatives."""

    DEFAULT_PBB_HALF: float = 28650.0  # 1/2 of Prisbasbelopp (2024: 57,300, 2025: 58,800)
    CORPORATE_TAX_RATE: float = 0.206   # 20.6% standard Swedish corporate income tax

    @classmethod
    def evaluate_vmb(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, VMBCalculation]]:
        """Evaluates whether a used trade-in machine should use VMB (ML 9a kap.) instead of 25% VAT."""
        if not tx.is_used_good or not tx.bought_from_private_individual:
            return None

        # Gross selling price and purchase cost
        sales_price_gross = tx.gross_amount
        purchase_cost = tx.purchase_cost_ex_vat
        gross_margin = sales_price_gross - purchase_cost

        if gross_margin <= 0:
            return None

        # 1. Suboptimal: Standard VAT 25% applied on full selling price
        standard_vat = round(sales_price_gross - (sales_price_gross / 1.25), 2)
        standard_profit = round((sales_price_gross / 1.25) - purchase_cost, 2)

        # 2. Optimal: VMB Margin Tax (20% of gross margin)
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
                legal_basis="Mervärdesskattelagen (1994:200 / 2023:200) 9a kap. Vinstmarginalbeskattning",
                recommended_bas_account="3051 Försäljning varor VMB",
                moms_box_change="Fält 05/10 -> Fält 08/10 (endast marginalen beskattas)",
                explanation=(
                    f"Inköpt från privatperson utan avdragsgill ingående moms. Genom att tillämpa VMB "
                    f"beskattas endast vinstmarginalen ({gross_margin:.0f} SEK) med 20%, vilket sparar "
                    f"{vat_saved:.2f} SEK i onödig utgående moms och ökar nettovinsten med {profit_pct:.1f}%."
                ),
            )
            return opp, calc

        return None

    @classmethod
    def evaluate_rut(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, RUTCalculation]]:
        """Evaluates whether an installation/service package qualifies for 50% RUT-avdrag."""
        if not tx.is_garden_or_installation_work and not tx.is_labor_service:
            return None

        # Check customer qualification (B2C private individual)
        if tx.customer and tx.customer.is_company:
            return None  # B2B companies do not qualify for RUT

        total_gross = tx.gross_amount
        labor_gross = tx.labor_share_amount if tx.labor_share_amount > 0 else (total_gross * 0.35)
        material_gross = total_gross - labor_gross

        rut_deduction = round(labor_gross * 0.50, 2)
        customer_payable_with_rut = round(total_gross - rut_deduction, 2)
        customer_saving_pct = round((rut_deduction / total_gross) * 100.0, 1)

        calc = RUTCalculation(
            total_package_gross=total_gross,
            material_cost_gross=material_gross,
            labor_cost_gross=labor_gross,
            standard_customer_payable=total_gross,
            standard_company_revenue=total_gross,
            rut_deduction_amount=rut_deduction,
            rut_customer_payable=customer_payable_with_rut,
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
                net_tax_saved_sek=0.0,  # tax rate remains 25%, but customer pays 50% less on labor
                net_profit_delta_sek=rut_deduction,  # perceived value & conversion driver
                legal_basis="Inkomstskattelagen 67 kap. Skattereduktion för hushållsarbete (RUT trädgårdsskötsel)",
                recommended_bas_account="3002 Försäljning arbetskostnad (med RUT-markering)",
                moms_box_change="Fält 05 & 10 (full moms redovisas, 50% arbetskostnad rekvireras från Skatteverket)",
                explanation=(
                    f"Installation/kabeldragning för robotgräsklippare på privat fastighet omfattas av RUT. "
                    f"Genom att erbjuda RUT betalar kunden {customer_payable_with_rut:.0f} SEK (sparar {rut_deduction:.0f} SEK, "
                    f"-{customer_saving_pct}%), medan företaget rekvirerar {rut_deduction:.0f} SEK från Skatteverket. "
                    f"Full intäkt och marginal bibehålls med avsevärt högre konverteringsgrad."
                ),
            )
            return opp, calc

        return None

    @classmethod
    def evaluate_reverse_charge_construction(cls, tx: TaxTransaction) -> Optional[TaxOptimizationOpportunity]:
        """Evaluates whether ground/cabling work for a construction company requires Reverse Charge VAT."""
        if not tx.is_garden_or_installation_work:
            return None

        customer = tx.customer
        if not customer or not customer.is_company or not customer.has_f_skatt:
            return None

        # SNI code starts with 41 (Byggande av bostadshus), 42 (Anläggningsarbeten), or 43 (Specialiserad bygg)
        is_construction_buyer = False
        if customer.sni_code:
            clean_sni = customer.sni_code.replace(".", "").strip()
            if clean_sni.startswith(("41", "42", "43")):
                is_construction_buyer = True

        if is_construction_buyer and tx.current_tax_rule == TaxRuleType.STANDARD_MOMS_25:
            vat_amount = tx.current_vat_amount
            return TaxOptimizationOpportunity(
                opportunity_id=f"rev_charge_opp_{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                applied_rule=TaxRuleType.STANDARD_MOMS_25,
                best_possible_rule=TaxRuleType.REVERSE_CHARGE_CONSTRUCTION,
                applied_tax_sek=vat_amount,
                best_possible_tax_sek=0.0,
                net_tax_saved_sek=vat_amount,
                net_profit_delta_sek=0.0,
                legal_basis="Mervärdesskattelagen 1 kap. 2 § första stycket 4 b (Omvänd skattskyldighet för byggtjänster)",
                recommended_bas_account="3231 Försäljning omvänd byggmoms",
                moms_box_change="Fält 05/10 -> Fält 41 (Försäljning när köparen är skattskyldig)",
                explanation=(
                    f"Köparen ({customer.name}, SNI {customer.sni_code}) är ett bygg/anläggningsföretag med F-skatt. "
                    f"Kabelgrävning och markarbete ska faktureras utan moms med lagtexten "
                    f"'Omvänd skattskyldighet för byggtjänster gäller'. Felaktig moms debiterad: {vat_amount:.2f} SEK."
                ),
            )

        return None

    @classmethod
    def evaluate_minor_asset_write_off(
        cls, tx: TaxTransaction, pbb_half: float = DEFAULT_PBB_HALF
    ) -> Optional[Tuple[TaxOptimizationOpportunity, AssetDepreciationEvaluation]]:
        """Evaluates whether equipment purchase qualifies for 100% direct write-off in Year 1."""
        if not tx.is_asset_purchase:
            return None

        cost_ex_vat = tx.net_amount
        qualifies = cost_ex_vat <= pbb_half

        year_1_direct = cost_ex_vat if qualifies else (cost_ex_vat / 5.0)
        year_1_deprec = cost_ex_vat / 5.0  # standard 5-year straight line

        tax_saving_direct = round(year_1_direct * cls.CORPORATE_TAX_RATE, 2)
        tax_saving_deprec = round(year_1_deprec * cls.CORPORATE_TAX_RATE, 2)
        cash_advantage = round(tax_saving_direct - tax_saving_deprec, 2)

        eval_model = AssetDepreciationEvaluation(
            purchase_price_ex_vat=cost_ex_vat,
            half_prisbasbelopp_threshold=pbb_half,
            qualifies_for_direct_write_off=qualifies,
            year_1_deduction_direct=year_1_direct,
            year_1_deduction_depreciation=year_1_deprec,
            year_1_tax_saving_direct=tax_saving_direct,
            year_1_tax_saving_depreciation=tax_saving_deprec,
            immediate_cash_retention_advantage=cash_advantage,
            recommended_account="5410 Förbrukningsinventarier" if qualifies else "1220 Maskiner och inventarier",
            recommended_treatment="Direktavskrivning år 1" if qualifies else "Avskrivning över 5 år",
        )

        if qualifies and tx.current_tax_rule != TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET:
            opp = TaxOptimizationOpportunity(
                opportunity_id=f"asset_write_off_{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                applied_rule=tx.current_tax_rule,
                best_possible_rule=TaxRuleType.DIRECT_WRITE_OFF_MINOR_ASSET,
                applied_tax_sek=tax_saving_deprec,
                best_possible_tax_sek=tax_saving_direct,
                net_tax_saved_sek=cash_advantage,
                net_profit_delta_sek=cash_advantage,
                legal_basis="Inkomstskattelagen 18 kap. 4 § (Direktavskrivning av inventarier av mindre värde < 1/2 PBB)",
                recommended_bas_account="5410 Förbrukningsinventarier",
                moms_box_change="N/A (Bokförs i resultaträkningen direkt istället för balansomslutning)",
                explanation=(
                    f"Inköp av verktyg/utrustning ({cost_ex_vat:.0f} SEK ex moms) understiger ett halvt prisbasbelopp "
                    f"({pbb_half:.0f} SEK). Genom direktavskrivning år 1 sparas {cash_advantage:.2f} SEK i bolagsskatt "
                    f"omedelbart och administration av avskrivningsplaner undviks."
                ),
            )
            return opp, eval_model

        return None

    @classmethod
    def evaluate_batch(cls, transactions: List[TaxTransaction]) -> TaxEvaluationResult:
        """Evaluates a batch of transactions and compiles an optimization report."""
        result = TaxEvaluationResult(total_evaluated_count=len(transactions))

        for tx in transactions:
            # 1. VMB Check
            vmb_res = cls.evaluate_vmb(tx)
            if vmb_res:
                opp, _ = vmb_res
                result.opportunities.append(opp)
                result.total_potential_savings_sek += opp.net_tax_saved_sek
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 2. RUT Check
            rut_res = cls.evaluate_rut(tx)
            if rut_res:
                opp, _ = rut_res
                result.opportunities.append(opp)
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 3. Reverse charge construction Check
            rev_opp = cls.evaluate_reverse_charge_construction(tx)
            if rev_opp:
                result.opportunities.append(rev_opp)
                result.compliance_risks_detected.append(
                    f"Tx {tx.transaction_id}: Construction buyer charged 25% VAT incorrectly. Reverse charge required."
                )

            # 4. Asset minor write-off Check
            asset_res = cls.evaluate_minor_asset_write_off(tx)
            if asset_res:
                opp, _ = asset_res
                result.opportunities.append(opp)
                result.total_potential_savings_sek += opp.net_tax_saved_sek
                result.total_profit_gain_sek += opp.net_profit_delta_sek

        result.total_potential_savings_sek = round(result.total_potential_savings_sek, 2)
        result.total_profit_gain_sek = round(result.total_profit_gain_sek, 2)
        return result
