"""Pydantic data models for Swedish Tax Evaluation and Bokföring."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ..core.types import TaxRuleType


class CustomerTaxProfile(BaseModel):
    """Customer tax attributes used for rule evaluation."""
    customer_id: str
    name: str
    is_company: bool = False
    org_nr: Optional[str] = None
    has_f_skatt: bool = False
    sni_code: Optional[str] = None  # e.g., '43.120' for construction/groundwork
    is_eu_business: bool = False
    eu_vat_nr: Optional[str] = None
    rut_eligible: bool = True  # private individuals with Swedish residency


class TaxTransaction(BaseModel):
    """Normalized financial transaction from Fortnox or Shopify."""
    transaction_id: str
    source_system: str  # 'FORTNOX', 'SHOPIFY', 'WORKSHOP_POS', 'INBYTE_FORM'
    description: str
    gross_amount: float
    net_amount: float
    current_vat_rate: float = 0.25
    current_vat_amount: float = 0.0
    current_tax_rule: TaxRuleType = TaxRuleType.STANDARD_MOMS_25
    
    # Context attributes
    is_used_good: bool = False
    purchase_cost_ex_vat: float = 0.0  # cost basis for trade-ins/VMB
    bought_from_private_individual: bool = False
    
    is_labor_service: bool = False
    is_garden_or_installation_work: bool = False
    labor_share_amount: float = 0.0
    material_share_amount: float = 0.0
    
    customer: Optional[CustomerTaxProfile] = None
    
    # Asset parameters (if an internal expense/purchase)
    is_asset_purchase: bool = False
    asset_expected_lifetime_years: int = 1


class VMBCalculation(BaseModel):
    """Detailed comparison between Normal VAT and VMB (ML 9a kap.)."""
    sales_price_gross: float
    purchase_cost: float
    gross_margin: float
    
    # Suboptimal / Standard VAT
    standard_vat_amount: float
    standard_profit_after_vat: float
    
    # Best Possible / VMB Margin Tax
    vmb_profit_margin: float
    vmb_vat_amount: float  # 20% of positive margin
    vmb_profit_after_vat: float
    
    # Deltas
    vat_saved_sek: float
    profit_increase_sek: float
    profit_increase_pct: float


class RUTCalculation(BaseModel):
    """RUT-avdrag calculation on robotic mower installation / garden work."""
    total_package_gross: float
    material_cost_gross: float
    labor_cost_gross: float
    
    # Standard pricing without RUT
    standard_customer_payable: float
    standard_company_revenue: float
    
    # Optimal pricing with RUT
    rut_deduction_amount: float  # 50% of labor
    rut_customer_payable: float
    skatteverket_payout_amount: float
    total_company_revenue_with_rut: float
    
    customer_saving_sek: float
    customer_saving_pct: float


class AssetDepreciationEvaluation(BaseModel):
    """Evaluation of equipment purchase against Prisbasbelopp (PBB) threshold."""
    purchase_price_ex_vat: float
    half_prisbasbelopp_threshold: float = 28650.0  # standard Swedish threshold
    qualifies_for_direct_write_off: bool
    
    year_1_deduction_direct: float
    year_1_deduction_depreciation: float
    
    year_1_tax_saving_direct: float  # assuming 20.6% corporate tax rate
    year_1_tax_saving_depreciation: float
    immediate_cash_retention_advantage: float
    recommended_account: str
    recommended_treatment: str


class MomsdeklarationReport(BaseModel):
    """Official Skatteverket Momsdeklaration Box Values."""
    period: str
    
    # Momspliktig försäljning som inte ingår i andra fält
    falt_05_momspliktig_forsaljning_25: float = 0.0
    falt_06_momspliktig_forsaljning_12: float = 0.0
    falt_07_momspliktig_forsaljning_6: float = 0.0
    
    # Hyresinkomster / VMB-marginal
    falt_08_vmb_marginal: float = 0.0
    
    # Utgående moms
    falt_10_utgaende_moms_25: float = 0.0
    falt_11_utgaende_moms_12: float = 0.0
    falt_12_utgaende_moms_6: float = 0.0
    
    # Försäljning när köparen är skattskyldig (Omvänd byggmoms)
    falt_41_omvand_byggmoms: float = 0.0
    
    # Försäljning av varor/tjänster till annat EU-land (OSS/Omvänd)
    falt_35_eu_forsaljning_varor: float = 0.0
    
    # Ingående moms
    falt_48_ingaende_moms: float = 0.0
    
    # Moms att betala eller få tillbaka
    falt_49_moms_att_betala_eller_fa_tillbaka: float = 0.0
