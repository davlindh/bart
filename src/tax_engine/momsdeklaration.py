"""Skatteverket Momsdeklaration aggregator and validator."""

from typing import List
from .models import TaxTransaction, MomsdeklarationReport
from ..core.types import TaxRuleType


class MomsdeklarationGenerator:
    """Aggregates transactions into official Skatteverket Momsdeklaration fields."""

    @classmethod
    def generate_report(cls, period: str, transactions: List[TaxTransaction], input_vat_total: float = 0.0) -> MomsdeklarationReport:
        report = MomsdeklarationReport(period=period)
        report.falt_48_ingaende_moms = round(input_vat_total, 2)

        for tx in transactions:
            if tx.current_tax_rule == TaxRuleType.STANDARD_MOMS_25:
                # 3001/3002 standard taxable sales
                report.falt_05_momspliktig_forsaljning_25 += tx.net_amount
                report.falt_10_utgaende_moms_25 += tx.current_vat_amount

            elif tx.current_tax_rule == TaxRuleType.REDUCED_MOMS_12:
                report.falt_06_momspliktig_forsaljning_12 += tx.net_amount
                report.falt_11_utgaende_moms_12 += tx.current_vat_amount

            elif tx.current_tax_rule == TaxRuleType.REDUCED_MOMS_6:
                report.falt_07_momspliktig_forsaljning_6 += tx.net_amount
                report.falt_12_utgaende_moms_6 += tx.current_vat_amount

            elif tx.current_tax_rule == TaxRuleType.VMB_MARGIN_TAX:
                # Under VMB, only the profit margin is reported in Fält 08
                margin = max(0.0, tx.gross_amount - tx.purchase_cost_ex_vat)
                # Margin includes VAT; ex-VAT portion of margin goes to Fält 08
                vmb_vat = round(margin * 0.20, 2)
                margin_ex_vat = round(margin - vmb_vat, 2)
                report.falt_08_vmb_marginal += margin_ex_vat
                report.falt_10_utgaende_moms_25 += vmb_vat

            elif tx.current_tax_rule == TaxRuleType.REVERSE_CHARGE_CONSTRUCTION:
                # 3231 goes to Fält 41 (0% output VAT)
                report.falt_41_omvand_byggmoms += tx.net_amount

        # Round all boxes
        report.falt_05_momspliktig_forsaljning_25 = round(report.falt_05_momspliktig_forsaljning_25, 2)
        report.falt_08_vmb_marginal = round(report.falt_08_vmb_marginal, 2)
        report.falt_10_utgaende_moms_25 = round(report.falt_10_utgaende_moms_25, 2)
        report.falt_41_omvand_byggmoms = round(report.falt_41_omvand_byggmoms, 2)

        # Total output VAT minus input VAT = Fält 49
        total_output_vat = (
            report.falt_10_utgaende_moms_25
            + report.falt_11_utgaende_moms_12
            + report.falt_12_utgaende_moms_6
        )
        report.falt_49_moms_att_betala_eller_fa_tillbaka = round(total_output_vat - report.falt_48_ingaende_moms, 2)

        return report
