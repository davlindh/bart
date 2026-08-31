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


class ROTCalculation(BaseModel):
    """ROT-avdrag calculation (30% on labor for renovation/conversion/extension)."""
    total_package_gross: float
    material_cost_gross: float
    labor_cost_gross: float
    
    standard_customer_payable: float
    standard_company_revenue: float
    
    rot_deduction_amount: float  # 30% of labor
    rot_customer_payable: float
    skatteverket_payout_amount: float
    total_company_revenue_with_rot: float
    
    customer_saving_sek: float
    customer_saving_pct: float


class GronTeknikCalculation(BaseModel):
    """Skattereduktion för grön teknik (Solceller 20%, Batteri 50%, Laddbox 50%)."""
    installation_type: str  # 'BATTERY_STORAGE' (50%), 'EV_CHARGING' (50%), 'SOLAR_PANELS' (20%)
    total_gross: float
    deduction_rate: float
    deduction_amount: float
    customer_payable: float
    skatteverket_claim: float
    customer_saving_sek: float


class PeriodiseringsfondCalculation(BaseModel):
    """Periodiseringsfond calculation (IL 30 kap.) — up to 25% profit deferral for AB."""
    taxable_profit_before_allocation: float
    max_allocation_rate: float = 0.25
    max_allocation_amount: float
    corporate_tax_rate: float = 0.206
    tax_deferral_benefit_sek: float
    max_deferral_years: int = 6
    reversal_year_schedule: Dict[str, float] = Field(default_factory=dict)


class K10Calculation(BaseModel):
    """K10 3:12 dividend room calculation (Förenklingsregeln vs Lönebaserat utrymme)."""
    fiscal_year: int
    forenklingsbelopp: float  # Standard schablon (approx 204,325 SEK for 2024, 209,550 for 2025)
    total_qualifying_wages: float = 0.0
    owner_wage: float = 0.0
    qualifies_for_wage_rule: bool = False
    wage_based_space: float = 0.0
    optimal_rule: str  # 'SCHABLON' vs 'LONEBASERAT'
    optimal_gransbelopp: float
    tax_at_20_pct: float
    comparison_vs_salary_tax_saving: float


class FoUCalculation(BaseModel):
    """FoU-avdrag calculation (R&D reduction on employer social contributions)."""
    rd_staff_hours: float
    rd_gross_salaries: float
    standard_social_fees: float  # 31.42%
    reduced_social_fees: float    # minus 10% reduction + 10% tax deduction on fees
    monthly_saving_sek: float
    annual_saving_sek: float


class TaxStrategyBundle(BaseModel):
    """A combined, conflict-free package of multiple tax cuts maximizing net cash & profitability."""
    bundle_id: str
    name: str
    description: str
    included_rule_types: List[TaxRuleType]
    opportunities: List[Any] = Field(default_factory=list)
    total_tax_saved_sek: float
    total_cash_retention_sek: float
    synergy_bonus_sek: float = 0.0
    net_economic_benefit_sek: float
    risk_level: str = "LOW"  # 'LOW', 'MEDIUM', 'HIGH'
    legal_references: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


class CombinationEvaluation(BaseModel):
    """Result of combinatorial optimization across all eligible tax strategies."""
    evaluated_strategies_count: int
    optimal_bundles: List[TaxStrategyBundle] = Field(default_factory=list)
    detected_conflicts: List[str] = Field(default_factory=list)
    synergy_opportunities: List[str] = Field(default_factory=list)
    max_combined_savings_sek: float = 0.0


class FinancialVerificationIssue(BaseModel):
    """Identified missing verification, audit trail break, or compliance discrepancy."""
    code: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    category: str  # 'BFL_BOKFORINGSLAGEN', 'ML_MOMS', 'SFL_SKATTEFORFARANDE', 'RECONCILIATION', 'EVIDENCE'
    title: str
    description: str
    affected_entity_id: Optional[str] = None
    remediation_suggestion: str
    legal_basis: str


class FinancialVerificationReport(BaseModel):
    """Audit verification report assessing financial integrity, source documents, and controls."""
    verification_score: float  # 0.0 to 1.0 (1.0 = flawless)
    total_checks_performed: int
    passed_checks_count: int
    issues: List[FinancialVerificationIssue] = Field(default_factory=list)
    reconciliations: Dict[str, bool] = Field(default_factory=dict)
    missing_source_documents_count: int = 0
    balanced_ledger_verified: bool = True
    recommendations: List[str] = Field(default_factory=list)


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
