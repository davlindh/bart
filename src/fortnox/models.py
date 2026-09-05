from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FortnoxCustomerType(str, Enum):
    PRIVATE = "PRIVATE"
    COMPANY = "COMPANY"


class FortnoxVATType(str, Enum):
    SEVAT = "SEVAT"
    SEREVERSEDVAT = "SEREVERSEDVAT"  # Omvänd byggmoms
    EUVAT = "EUVAT"
    EXPORT = "EXPORT"


class FortnoxCustomer(BaseModel):
    """Fortnox Customer entity corresponding to Fortnox API /3/customers."""
    customer_number: str
    name: str
    customer_type: FortnoxCustomerType = FortnoxCustomerType.PRIVATE
    organisation_number: Optional[str] = None  # Org.nr or Personnummer
    vat_type: FortnoxVATType = FortnoxVATType.SEVAT
    vat_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address1: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    payment_terms_days: int = 14
    credit_limit: float = 50000.0
    rut_eligible: bool = True
    has_f_skatt: bool = False
    sni_code: Optional[str] = None  # e.g., '43.120' for construction/groundwork
    property_designation: Optional[str] = None  # Fastighetsbeteckning för ROT/RUT
    active: bool = True
    registered_machines: List[Dict[str, Any]] = Field(default_factory=list)
    rut_used_this_year: float = 0.0
    rut_remaining_quota: float = 75000.0



class FortnoxInvoiceRow(BaseModel):
    article_number: str
    description: str
    delivered_quantity: float
    price: float
    vat: float  # VAT percentage e.g. 25, 12, 6, 0
    account_number: int = 3001
    cost_center: Optional[str] = None
    project: Optional[str] = None
    is_work_cost: bool = False  # Arbetskostnad för ROT/RUT


class FortnoxInvoice(BaseModel):
    document_number: str
    customer_number: str
    customer_name: str
    invoice_date: str
    due_date: str
    total: float
    net: float
    vat_included: bool = True
    rows: List[FortnoxInvoiceRow] = Field(default_factory=list)
    project: Optional[str] = None
    cost_center: Optional[str] = None
    is_paid: bool = False
    payment_date: Optional[str] = None


class FortnoxEmployee(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    personal_identity_number: Optional[str] = None
    job_title: str
    department: str = "Verkstad & Service"
    monthly_salary: float = 35000.0
    hourly_wage: Optional[float] = None
    is_owner: bool = False
    is_rd_personnel: bool = False


class FortnoxTimeReport(BaseModel):
    report_id: str
    employee_id: str
    date: str
    project_code: str
    cost_center: str = "DRIFT"
    hours: float
    activity: str  # e.g., 'Installation', 'Verkstadsarbete', 'Utveckling', 'Felsökning'
    is_overtime: bool = False


class FortnoxProject(BaseModel):
    project_code: str
    description: str
    status: str = "ONGOING"  # ONGOING, COMPLETED, PAUSED
    start_date: str
    end_date: Optional[str] = None
    project_leader_id: str


class FortnoxVoucherRow(BaseModel):
    account: int
    description: str
    debet: float = 0.0
    kredit: float = 0.0
    account_name: Optional[str] = None
    vat_code: Optional[str] = None


class FortnoxVoucher(BaseModel):
    voucher_number: int
    voucher_series: str = "A"
    description: str
    transaction_date: str
    rows: List[FortnoxVoucherRow] = Field(default_factory=list)
    total_debet: float = 0.0
    total_kredit: float = 0.0
    is_balanced: bool = True
    skatteverket_report_boxes: Dict[str, float] = Field(default_factory=dict)
