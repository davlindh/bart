"""Swedish BAS-kontoplan definitions and automated double-entry journal generation."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class LedgerAccount(BaseModel):
    """BAS Account metadata."""
    account_number: str
    name: str
    account_type: str  # ASSET, LIABILITY, EQUITY, REVENUE, DIRECT_COST, EXPENSE
    vat_code: Optional[str] = None
    moms_box: Optional[str] = None


class JournalRow(BaseModel):
    """Single debit or credit entry row in a Swedish accounting voucher (verifikat)."""
    account: str
    account_name: str
    debet: float = 0.0
    kredit: float = 0.0
    description: str = ""


class JournalEntry(BaseModel):
    """Complete balanced accounting voucher (Verifikat)."""
    verifikat_id: str
    series: str = "A"
    description: str
    date: str
    rows: List[JournalRow] = Field(default_factory=list)
    total_debet: float = 0.0
    total_kredit: float = 0.0
    is_balanced: bool = False

    def validate_and_balance(self) -> bool:
        """Ensures that Debet == Kredit (double-entry bookkeeping requirement)."""
        self.total_debet = round(sum(r.debet for r in self.rows), 2)
        self.total_kredit = round(sum(r.kredit for r in self.rows), 2)
        self.is_balanced = abs(self.total_debet - self.total_kredit) < 0.01
        return self.is_balanced


class BASKontoplan:
    """Standard BAS-kontoplan accounts for retail, machinery e-commerce, and workshop."""

    ACCOUNTS: Dict[str, LedgerAccount] = {
        "1510": LedgerAccount(account_number="1510", name="Kundfordringar", account_type="ASSET"),
        "1580": LedgerAccount(account_number="1580", name="Fordran hos betalningsförmedlare (Shopify/Klarna)", account_type="ASSET"),
        "1910": LedgerAccount(account_number="1910", name="Kassa (Butik)", account_type="ASSET"),
        "1930": LedgerAccount(account_number="1930", name="Företagskonto / Checkräkning", account_type="ASSET"),
        "2611": LedgerAccount(account_number="2611", name="Utgående moms 25%", account_type="LIABILITY", vat_code="MP1", moms_box="10"),
        "2621": LedgerAccount(account_number="2621", name="Utgående moms 12%", account_type="LIABILITY", vat_code="MP2", moms_box="11"),
        "2631": LedgerAccount(account_number="2631", name="Utgående moms 6%", account_type="LIABILITY", vat_code="MP3", moms_box="12"),
        "2641": LedgerAccount(account_number="2641", name="Debiterad ingående moms", account_type="ASSET", vat_code="IN", moms_box="48"),
        "2650": LedgerAccount(account_number="2650", name="Redovisningskonto för moms", account_type="LIABILITY", moms_box="49"),
        "3001": LedgerAccount(account_number="3001", name="Försäljning varor 25% moms", account_type="REVENUE", moms_box="05"),
        "3002": LedgerAccount(account_number="3002", name="Försäljning verkstad/arbetskostnad 25%", account_type="REVENUE", moms_box="05"),
        "3051": LedgerAccount(account_number="3051", name="Försäljning varor VMB (marginalbeskattat)", account_type="REVENUE", moms_box="08"),
        "3231": LedgerAccount(account_number="3231", name="Försäljning tjänster omvänd skattskyldighet bygg", account_type="REVENUE", moms_box="41"),
        "4000": LedgerAccount(account_number="4000", name="Inköp av varor för vidareförsäljning", account_type="DIRECT_COST"),
        "5410": LedgerAccount(account_number="5410", name="Förbrukningsinventarier (< 1/2 PBB)", account_type="EXPENSE"),
        "6040": LedgerAccount(account_number="6040", name="Kontokorts- och betalningsavgifter", account_type="EXPENSE"),
        "2110": LedgerAccount(account_number="2110", name="Periodiseringsfonder", account_type="EQUITY"),
    }

    @classmethod
    def get_account(cls, account_number: str) -> LedgerAccount:
        if account_number in cls.ACCOUNTS:
            return cls.ACCOUNTS[account_number]
        return LedgerAccount(account_number=account_number, name=f"Konto {account_number}", account_type="OTHER")

    @classmethod
    def create_shopify_settlement_voucher(
        cls,
        verifikat_id: str,
        gross_sales: float,
        clearing_fee: float,
        payout_net: float,
        date: str = "2026-08-27"
    ) -> JournalEntry:
        """Creates balanced voucher for Shopify/Klarna batch settlement payout to bank."""
        entry = JournalEntry(
            verifikat_id=verifikat_id,
            description="Shopify/Klarna Avräkning & Utbetalning till Bank",
            date=date,
            rows=[
                JournalRow(account="1930", account_name="Företagskonto", debet=payout_net, kredit=0.0, description="Nettoinsättning från betalväxel"),
                JournalRow(account="6040", account_name="Betalningsavgifter", debet=clearing_fee, kredit=0.0, description="Transaktionsavgift"),
                JournalRow(account="1580", account_name="Fordran betalväxel", debet=0.0, kredit=gross_sales, description="Avräkning kundfordran"),
            ]
        )
        entry.validate_and_balance()
        return entry

    @classmethod
    def create_vmb_sale_voucher(
        cls,
        verifikat_id: str,
        selling_price_gross: float,
        purchase_cost: float,
        vmb_vat: float,
        payment_method_account: str = "1580",
        date: str = "2026-08-27"
    ) -> JournalEntry:
        """Creates balanced voucher for sale of used machine under VMB (ML 9a kap.)."""
        # Net revenue booked = selling price minus VMB VAT
        net_revenue = round(selling_price_gross - vmb_vat, 2)
        entry = JournalEntry(
            verifikat_id=verifikat_id,
            description="Försäljning begagnad maskin enligt VMB (ML 9a kap)",
            date=date,
            rows=[
                JournalRow(account=payment_method_account, account_name="Betalningsmottagare", debet=selling_price_gross, kredit=0.0, description="Kundinbetalning"),
                JournalRow(account="3051", account_name="Försäljning varor VMB", debet=0.0, kredit=net_revenue, description="Nettointäkt VMB"),
                JournalRow(account="2611", account_name="Utgående moms VMB", debet=0.0, kredit=vmb_vat, description="Moms 20% på vinstmarginal"),
            ]
        )
        entry.validate_and_balance()
        return entry
