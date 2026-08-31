"""Fortnox API Data Models: Pydantic schemas for Fortnox ERP entities.
Covers Invoices, Employees, Salaries, Time-reports, Projects, Cost Centers, and Vouchers.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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


class FortnoxVoucher(BaseModel):
    voucher_number: int
    voucher_series: str = "A"
    description: str
    transaction_date: str
    rows: List[FortnoxVoucherRow] = Field(default_factory=list)
