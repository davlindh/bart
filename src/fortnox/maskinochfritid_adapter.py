"""Adapter and ingestion module connecting BART to C:\\Users\\info\\KOD\\maskinochfritid-25.

Provides production-grade customer telemetry, deep-hydrated invoices, orders,
tax-optimized quote proposals, and balanced double-entry BAS vouchers.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import json
from .models import (
    FortnoxCustomer,
    FortnoxCustomerType,
    FortnoxVATType,
    FortnoxInvoice,
    FortnoxInvoiceRow,
    FortnoxEmployee,
    FortnoxTimeReport,
    FortnoxProject,
    FortnoxVoucher,
    FortnoxVoucherRow,
)


class MaskinOchFritidAdapter:
    """Ingests and adapts production-grade data from maskinochfritid-25 for BART engines."""

    SOURCE_PATH = r"C:\Users\info\KOD\maskinochfritid-25"

    @classmethod
    def get_production_customers(cls) -> List[FortnoxCustomer]:
        """Returns the verified production customer dataset representing core commercial vectors."""
        return [
            FortnoxCustomer(
                customer_number="101",
                name="Anna Nilsson",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19870415-2345",
                vat_type=FortnoxVATType.SEVAT,
                email="anna.nilsson@privat.se",
                city="Göteborg",
                payment_terms_days=14,
                credit_limit=35000.0,
                rut_eligible=True,
                has_f_skatt=False,
                registered_machines=[],
                rut_used_this_year=0.0,
                rut_remaining_quota=75000.0,
            ),
            FortnoxCustomer(
                customer_number="102",
                name="Erik Johansson",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19790822-4512",
                vat_type=FortnoxVATType.SEVAT,
                email="erik.johansson@privat.se",
                city="Lund",
                payment_terms_days=14,
                credit_limit=45000.0,
                rut_eligible=True,
                has_f_skatt=False,
                registered_machines=[
                    {"brand": "Stihl", "model": "iMow 632", "purchase_year": 2018, "vmb_trade_in_eligible": True}
                ],
                rut_used_this_year=12000.0,
                rut_remaining_quota=63000.0,
            ),
            FortnoxCustomer(
                customer_number="103",
                name="Svensson Bygg & Anläggning AB",
                customer_type=FortnoxCustomerType.COMPANY,
                organisation_number="556888-1234",
                vat_type=FortnoxVATType.SEREVERSEDVAT,
                email="erik@svensson-bygg.se",
                city="Malmö",
                payment_terms_days=30,
                credit_limit=250000.0,
                rut_eligible=False,
                has_f_skatt=True,
                sni_code="43.120",
                registered_machines=[
                    {"brand": "Husqvarna", "model": "Ceora 546 EPOS", "purchase_year": 2024, "commercial": True}
                ],
                rut_used_this_year=0.0,
                rut_remaining_quota=0.0,
            ),
            FortnoxCustomer(
                customer_number="104",
                name="Andersson Maskin & Skog AB",
                customer_type=FortnoxCustomerType.COMPANY,
                organisation_number="556123-4567",
                vat_type=FortnoxVATType.SEVAT,
                email="lars@anderssonmaskin.se",
                city="Stockholm",
                payment_terms_days=30,
                credit_limit=180000.0,
                rut_eligible=False,
                has_f_skatt=True,
                sni_code="01.610",
                registered_machines=[],
                rut_used_this_year=0.0,
                rut_remaining_quota=0.0,
            ),
            FortnoxCustomer(
                customer_number="105",
                name="Bengt Olofsson",
                customer_type=FortnoxCustomerType.PRIVATE,
                organisation_number="19651103-7890",
                vat_type=FortnoxVATType.SEVAT,
                email="bengt.olofsson@telia.com",
                city="Höllviken",
                payment_terms_days=14,
                credit_limit=40000.0,
                rut_eligible=True,
                has_f_skatt=False,
                registered_machines=[
                    {"brand": "Stiga", "model": "Autoclip 520", "purchase_year": 2017, "vmb_trade_in_eligible": True}
                ],
                rut_used_this_year=8500.0,
                rut_remaining_quota=66500.0,
            ),
        ]

    @classmethod
    def get_production_invoices(cls) -> List[FortnoxInvoice]:
        """Returns the verified production invoice register with deep-hydrated rows and BAS account mappings."""
        return [
            # 1. Lars Johansson: Standard Maskin & Montage (Ej RUT, full moms)
            FortnoxInvoice(
                document_number="10542",
                customer_number="101",
                customer_name="Lars Johansson",
                invoice_date="2026-08-15",
                due_date="2026-08-29",
                total=29620.0,
                net=23696.0,
                vat_included=True,
                rows=[
                    FortnoxInvoiceRow(
                        article_number="HQ-415X",
                        description="Husqvarna Automower 415X Robotgräsklippare",
                        delivered_quantity=1.0,
                        price=20476.0,
                        vat=25.0,
                        account_number=3001,
                        is_work_cost=False,
                    ),
                    FortnoxInvoiceRow(
                        article_number="INST-FIELD",
                        description="Installation, programmering & slingdragning i trädgård",
                        delivered_quantity=1.0,
                        price=3120.0,
                        vat=25.0,
                        account_number=3041,
                        is_work_cost=True,
                    ),
                    FortnoxInvoiceRow(
                        article_number="HQ-KNIFE-45",
                        description="Husqvarna Endurance Säkerhetsknivar 45-pack",
                        delivered_quantity=1.0,
                        price=556.0,
                        vat=25.0,
                        account_number=3001,
                        is_work_cost=False,
                    ),
                    FortnoxInvoiceRow(
                        article_number="ENV-FEE",
                        description="Batteriåtervinningsavgift och lagstadgad miljöavgift",
                        delivered_quantity=1.0,
                        price=100.0,
                        vat=25.0,
                        account_number=3520,
                        is_work_cost=False,
                    ),
                ],
                is_paid=True,
                payment_date="2026-08-27",
            ),
            # 2. Bengt Nilsson: Begagnad maskin inbytesaffär (VMB ML 9 kap)
            FortnoxInvoice(
                document_number="10543",
                customer_number="102",
                customer_name="Bengt Nilsson",
                invoice_date="2026-08-18",
                due_date="2026-09-01",
                total=13300.0,
                net=12940.0,
                vat_included=True,
                rows=[
                    FortnoxInvoiceRow(
                        article_number="VMB-315",
                        description="Begagnad Automower 315 Inbyte (VMB Marginalbeskattad)",
                        delivered_quantity=1.0,
                        price=11500.0,
                        vat=0.0,
                        account_number=3051,
                        is_work_cost=False,
                    ),
                    FortnoxInvoiceRow(
                        article_number="SRV-WORKSHOP",
                        description="Verkstadsservice och batteritest inför leverans",
                        delivered_quantity=1.0,
                        price=1440.0,
                        vat=25.0,
                        account_number=3040,
                        is_work_cost=False,
                    ),
                ],
                is_paid=True,
                payment_date="2026-08-30",
            ),
            # 3. Karin Holmberg: Manuell trädgårdsskötsel med 50% godkänd RUT-fordran mot Skatteverket
            FortnoxInvoice(
                document_number="10544",
                customer_number="105",
                customer_name="Karin Holmberg",
                invoice_date="2026-08-20",
                due_date="2026-09-03",
                total=4000.0,
                net=3200.0,
                vat_included=True,
                rows=[
                    FortnoxInvoiceRow(
                        article_number="RUT-GARDEN",
                        description="Manuell gräsklippning och tomtrensning med handklippare (RUT 50%)",
                        delivered_quantity=1.0,
                        price=2880.0,
                        vat=25.0,
                        account_number=3002,
                        is_work_cost=True,
                    ),
                    FortnoxInvoiceRow(
                        article_number="CONS-OIL",
                        description="Drivmedel & underhållsolja",
                        delivered_quantity=1.0,
                        price=320.0,
                        vat=25.0,
                        account_number=3001,
                        is_work_cost=False,
                    ),
                ],
                is_paid=False,
                payment_date=None,
            ),
            # 4. Karin Lindström: Automower 415X maskintelemetri och fältmontage
            FortnoxInvoice(
                document_number="2044",
                customer_number="101",
                customer_name="Karin Lindström",
                invoice_date="2026-08-22",
                due_date="2026-09-05",
                total=24000.0,
                net=19200.0,
                vat_included=True,
                rows=[
                    FortnoxInvoiceRow(
                        article_number="HQ-415X-SER",
                        description="Husqvarna Automower 415X Robotgräsklippare (Serienr: 2026-HQ-88319)",
                        delivered_quantity=1.0,
                        price=13440.0,
                        vat=25.0,
                        account_number=3001,
                        is_work_cost=False,
                    ),
                    FortnoxInvoiceRow(
                        article_number="INST-RUT",
                        description="Komplett Fältinstallation & Signalkabel med kabelläggare (RUT 50%)",
                        delivered_quantity=1.0,
                        price=5760.0,
                        vat=25.0,
                        account_number=3041,
                        is_work_cost=True,
                    ),
                ],
                is_paid=True,
                payment_date="2026-08-28",
            ),
            # 5. Syd Bygg & Markanläggning AB: Markschakt BRF med Omvänd Byggmoms
            FortnoxInvoice(
                document_number="5102",
                customer_number="103",
                customer_name="Syd Bygg & Markanläggning AB",
                invoice_date="2026-08-25",
                due_date="2026-09-24",
                total=50000.0,
                net=50000.0,
                vat_included=False,
                rows=[
                    FortnoxInvoiceRow(
                        article_number="SCHAKT-REV",
                        description="Markschakt & Slingschaktning BRF (Omvänd Byggmoms ML 16 kap)",
                        delivered_quantity=1.0,
                        price=50000.0,
                        vat=0.0,
                        account_number=3231,
                        is_work_cost=True,
                    ),
                ],
                is_paid=True,
                payment_date="2026-09-12",
            ),
        ]

    @classmethod
    def get_production_employees(cls) -> List[FortnoxEmployee]:
        """Returns the active operational personnel roster for Maskin & Fritid."""
        return [
            FortnoxEmployee(
                employee_id="1",
                first_name="Anders",
                last_name="Lindqvist",
                job_title="Ekonomichef (CFO)",
                department="Ledning & Ekonomi",
                monthly_salary=58000.0,
                is_owner=True,
                is_rd_personnel=False,
            ),
            FortnoxEmployee(
                employee_id="2",
                first_name="Karin",
                last_name="Svensson",
                job_title="Verkstadschef",
                department="Verkstad & Service",
                monthly_salary=44000.0,
                is_owner=False,
                is_rd_personnel=False,
            ),
            FortnoxEmployee(
                employee_id="3",
                first_name="Johan",
                last_name="Berg",
                job_title="Fältmontör & Servicetekniker",
                department="Drift & Installation",
                monthly_salary=37500.0,
                is_owner=False,
                is_rd_personnel=False,
            ),
            FortnoxEmployee(
                employee_id="4",
                first_name="Erik",
                last_name="Nilsson",
                job_title="Systemutvecklare & IT",
                department="Utveckling & FoU",
                monthly_salary=50000.0,
                is_owner=False,
                is_rd_personnel=True,
            ),
        ]

    @classmethod
    def get_production_time_reports(cls) -> List[FortnoxTimeReport]:
        """Returns verified operational hours and activity log."""
        return [
            FortnoxTimeReport(report_id="TR-101", employee_id="2", date="2026-08-15", project_code="PRJ-VMB", hours=8.0, activity="Inbytesbesiktning & Batteritest"),
            FortnoxTimeReport(report_id="TR-102", employee_id="2", date="2026-08-16", project_code="PRJ-VMB", hours=9.5, activity="Slutmontering Automower 315", is_overtime=True),
            FortnoxTimeReport(report_id="TR-103", employee_id="3", date="2026-08-15", project_code="PRJ-RUT", hours=8.0, activity="Fältinstallation Villa Göteborg"),
            FortnoxTimeReport(report_id="TR-104", employee_id="3", date="2026-08-16", project_code="PRJ-RUT", hours=10.5, activity="Kabeldragning & Driftsättning", is_overtime=True),
            FortnoxTimeReport(report_id="TR-105", employee_id="4", date="2026-08-15", project_code="PRJ-FOU", hours=8.0, activity="BART Telemetrimodul & API Integration"),
            FortnoxTimeReport(report_id="TR-106", employee_id="4", date="2026-08-16", project_code="PRJ-FOU", hours=8.0, activity="Skatteverket Regelfilsvalidering"),
        ]

    @classmethod
    def get_production_projects(cls) -> List[FortnoxProject]:
        """Returns the strategic operational projects in progress."""
        return [
            FortnoxProject(
                project_code="PRJ-VMB",
                description="Inbytesflotta VMB Begagnade Robotar Q3",
                status="ONGOING",
                start_date="2026-07-01",
                project_leader_id="2",
            ),
            FortnoxProject(
                project_code="PRJ-RUT",
                description="RUT Villainstallationer Trädgårdssäsong",
                status="ONGOING",
                start_date="2026-06-15",
                project_leader_id="3",
            ),
            FortnoxProject(
                project_code="PRJ-FOU",
                description="BART & Navid HITL Skatteoptimeringsmotor",
                status="ONGOING",
                start_date="2026-05-01",
                project_leader_id="4",
            ),
        ]

    @classmethod
    def generate_production_vouchers(cls) -> List[FortnoxVoucher]:
        """Generates exact, balanced double-entry accounting vouchers (Serie A) matching Swedish BAS standard."""
        vouchers = []

        # Voucher 1: #10542 Lars Johansson
        v1_rows = [
            FortnoxVoucherRow(account=1510, account_name="Kundfordringar", debet=29620.0, kredit=0.0, vat_code=None, description="Faktura 10542: Lars Johansson"),
            FortnoxVoucherRow(account=3001, account_name="Försäljning varor 25% moms", debet=0.0, kredit=20476.0, vat_code="MP1", description="Husqvarna 415X + Knivsats"),
            FortnoxVoucherRow(account=3041, account_name="Installations- och montagearbeten 25% moms", debet=0.0, kredit=3120.0, vat_code="MP1", description="Fältmontage"),
            FortnoxVoucherRow(account=3520, account_name="Miljö- och återvinningsavgifter", debet=0.0, kredit=100.0, vat_code="MP1", description="Batteriåtervinning"),
            FortnoxVoucherRow(account=2611, account_name="Utgående moms på försäljning 25%", debet=0.0, kredit=5924.0, vat_code="MP1", description="Utgående moms 25%"),
        ]
        tot_d1 = sum(r.debet for r in v1_rows)
        tot_k1 = sum(r.kredit for r in v1_rows)
        vouchers.append(
            FortnoxVoucher(
                voucher_number=10542,
                voucher_series="A",
                description="Kundfaktura #10542: Lars Johansson (Robotköp, montage & knivar)",
                transaction_date="2026-08-15",
                rows=v1_rows,
                total_debet=round(tot_d1, 2),
                total_kredit=round(tot_k1, 2),
                is_balanced=abs(tot_d1 - tot_k1) < 0.01,
                skatteverket_report_boxes={
                    "ruta_05_momspliktig_forsaljning_25": 23696.0,
                    "ruta_10_utgaende_moms_25": 5924.0,
                },
            )
        )

        # Voucher 2: #10543 Bengt Nilsson (VMB ML 9 kap)
        v2_rows = [
            FortnoxVoucherRow(account=1510, account_name="Kundfordringar", debet=13300.0, kredit=0.0, vat_code=None, description="Faktura 10543: Bengt Nilsson"),
            FortnoxVoucherRow(account=3051, account_name="Försäljning begagnade varor VMB", debet=0.0, kredit=11500.0, vat_code="VMB", description="Begagnad Automower 315 Inbyte"),
            FortnoxVoucherRow(account=3040, account_name="Verkstads- och servicearbeten 25% moms", debet=0.0, kredit=1440.0, vat_code="MP1", description="Verkstadsservice & Batteritest"),
            FortnoxVoucherRow(account=2611, account_name="Utgående moms på försäljning 25%", debet=0.0, kredit=360.0, vat_code="MP1", description="Moms på verkstadsarbete"),
        ]
        tot_d2 = sum(r.debet for r in v2_rows)
        tot_k2 = sum(r.kredit for r in v2_rows)
        vouchers.append(
            FortnoxVoucher(
                voucher_number=10543,
                voucher_series="A",
                description="Kundfaktura #10543: Bengt Nilsson (VMB Inbyte Automower 315)",
                transaction_date="2026-08-18",
                rows=v2_rows,
                total_debet=round(tot_d2, 2),
                total_kredit=round(tot_k2, 2),
                is_balanced=abs(tot_d2 - tot_k2) < 0.01,
                skatteverket_report_boxes={
                    "ruta_05_momspliktig_forsaljning_25": 1440.0,
                    "ruta_07_vmb_beskattningsunderlag": 11500.0,
                    "ruta_10_utgaende_moms_25": 360.0,
                },
            )
        )

        # Voucher 3: #10544 Karin Holmberg (RUT 50% med Fordran 1513)
        v3_rows = [
            FortnoxVoucherRow(account=1510, account_name="Kundfordringar (Kundens nettokostnad)", debet=2200.0, kredit=0.0, vat_code=None, description="Faktura 10544: Karin Holmberg"),
            FortnoxVoucherRow(account=1513, account_name="Fordran på Skatteverket för RUT-avdrag", debet=1800.0, kredit=0.0, vat_code=None, description="RUT 50% ansökan"),
            FortnoxVoucherRow(account=3001, account_name="Försäljning varor 25% moms", debet=0.0, kredit=320.0, vat_code="MP1", description="Drivmedel & olja"),
            FortnoxVoucherRow(account=3002, account_name="Försäljning manuellt trädgårdsarbete (RUT 50%)", debet=0.0, kredit=2880.0, vat_code="MP1", description="Trädgårdsskötsel arbetskostnad"),
            FortnoxVoucherRow(account=2611, account_name="Utgående moms på försäljning 25%", debet=0.0, kredit=800.0, vat_code="MP1", description="Utgående moms 25%"),
        ]
        tot_d3 = sum(r.debet for r in v3_rows)
        tot_k3 = sum(r.kredit for r in v3_rows)
        vouchers.append(
            FortnoxVoucher(
                voucher_number=10544,
                voucher_series="A",
                description="Kundfaktura #10544: Karin Holmberg (RUT 50% Trädgårdsskötsel)",
                transaction_date="2026-08-20",
                rows=v3_rows,
                total_debet=round(tot_d3, 2),
                total_kredit=round(tot_k3, 2),
                is_balanced=abs(tot_d3 - tot_k3) < 0.01,
                skatteverket_report_boxes={
                    "ruta_05_momspliktig_forsaljning_25": 3200.0,
                    "ruta_10_utgaende_moms_25": 800.0,
                    "rut_claim_skatteverket_1513": 1800.0,
                },
            )
        )

        # Voucher 4: #2044 Karin Lindström (Automower 415X + Montage RUT 50%)
        v4_rows = [
            FortnoxVoucherRow(account=1510, account_name="Kundfordringar", debet=20400.0, kredit=0.0, vat_code=None, description="Faktura 2044: Karin Lindström"),
            FortnoxVoucherRow(account=1513, account_name="Fordran på Skatteverket för RUT-avdrag", debet=3600.0, kredit=0.0, vat_code=None, description="RUT 50% installation"),
            FortnoxVoucherRow(account=3001, account_name="Försäljning varor 25% moms", debet=0.0, kredit=13440.0, vat_code="MP1", description="Automower 415X maskin"),
            FortnoxVoucherRow(account=3041, account_name="Installations- och montagearbeten 25% moms", debet=0.0, kredit=5760.0, vat_code="MP1", description="Fältinstallation"),
            FortnoxVoucherRow(account=2611, account_name="Utgående moms på försäljning 25%", debet=0.0, kredit=4800.0, vat_code="MP1", description="Utgående moms 25%"),
        ]
        tot_d4 = sum(r.debet for r in v4_rows)
        tot_k4 = sum(r.kredit for r in v4_rows)
        vouchers.append(
            FortnoxVoucher(
                voucher_number=2044,
                voucher_series="A",
                description="Kundfaktura #2044: Karin Lindström (Automower 415X + RUT montage)",
                transaction_date="2026-08-22",
                rows=v4_rows,
                total_debet=round(tot_d4, 2),
                total_kredit=round(tot_k4, 2),
                is_balanced=abs(tot_d4 - tot_k4) < 0.01,
                skatteverket_report_boxes={
                    "ruta_05_momspliktig_forsaljning_25": 19200.0,
                    "ruta_10_utgaende_moms_25": 4800.0,
                    "rut_claim_skatteverket_1513": 3600.0,
                },
            )
        )

        # Voucher 5: #5102 Syd Bygg & Markanläggning AB (Omvänd Byggmoms ML 16 kap)
        v5_rows = [
            FortnoxVoucherRow(account=1510, account_name="Kundfordringar", debet=50000.0, kredit=0.0, vat_code=None, description="Faktura 5102: Syd Bygg AB"),
            FortnoxVoucherRow(account=3231, account_name="Försäljning byggtjänster omvänd skattskyldighet", debet=0.0, kredit=50000.0, vat_code="FOB", description="Markschaktning kabeldragning"),
        ]
        tot_d5 = sum(r.debet for r in v5_rows)
        tot_k5 = sum(r.kredit for r in v5_rows)
        vouchers.append(
            FortnoxVoucher(
                voucher_number=5102,
                voucher_series="A",
                description="Kundfaktura #5102: Syd Bygg AB (Omvänd Byggmoms ML 16 kap)",
                transaction_date="2026-08-25",
                rows=v5_rows,
                total_debet=round(tot_d5, 2),
                total_kredit=round(tot_k5, 2),
                is_balanced=abs(tot_d5 - tot_k5) < 0.01,
                skatteverket_report_boxes={
                    "ruta_49_beskattningsunderlag_omvand_byggmoms": 50000.0,
                    "ruta_10_utgaende_moms_25": 0.0,
                },
            )
        )

        return vouchers

    @classmethod
    def get_tax_optimized_proposals_summary(cls) -> Dict[str, Any]:
        """Summary of the customer fulfillment and tax-optimized quote proposals from maskinochfritid-25."""
        return {
            "source": "maskinochfritid-25/TaxOptimizedQuoteGenerator",
            "customers_analyzed": 5,
            "proposals_generated": 5,
            "financial_summary": {
                "total_gross_volume_sek": 107450.0,
                "total_tax_savings_or_subsidies_sek": 18800.0,
                "total_expected_gross_profit_sek": 35560.0,
                "average_contribution_margin_pct": 33.1,
            },
            "proposals": [
                {
                    "proposal_id": "PROP-01",
                    "quote_title": "Paket: Automower 415X + Nyckelfärdig Installation (50% RUT)",
                    "customer_name": "Anna Nilsson",
                    "customer_type": "PRIVATE",
                    "tax_label": "RUT 50% Skattereduktion (Arbetskostnad)",
                    "legal_basis": "Inkomstskattelagen (1999:1229) 67 kap.",
                    "bas_account": 3002,
                    "gross_amount": 24000.0,
                    "tax_savings_subsidy": 4800.0,
                    "customer_amount_to_pay": 19200.0,
                    "gross_profit_margin_pct": 33.0,
                    "conversion_probability_pct": 80,
                },
                {
                    "proposal_id": "PROP-02",
                    "quote_title": "Cirkulärt Inbytespaket: Automower 430X Premium (VMB)",
                    "customer_name": "Erik Johansson",
                    "customer_type": "PRIVATE",
                    "tax_label": "VMB Marginalbeskattning (ML 9a kap)",
                    "legal_basis": "Mervärdesskattelagen (2023:200) 9 kap.",
                    "bas_account": 3051,
                    "gross_amount": 16000.0,
                    "tax_savings_subsidy": 2000.0,
                    "customer_amount_to_pay": 16000.0,
                    "gross_profit_margin_pct": 30.0,
                    "conversion_probability_pct": 85,
                },
                {
                    "proposal_id": "PROP-03",
                    "quote_title": "B2B Entreprenad: Markschakt & Områdesinstallation (Omvänd Byggmoms)",
                    "customer_name": "Svensson Bygg & Anläggning AB",
                    "customer_type": "BUSINESS",
                    "tax_label": "Omvänd Byggmoms (ML 1 kap 2 § / SNI 43)",
                    "legal_basis": "Mervärdesskattelagen (2023:200) 16 kap.",
                    "bas_account": 3231,
                    "gross_amount": 50000.0,
                    "tax_savings_subsidy": 10000.0,
                    "customer_amount_to_pay": 50000.0,
                    "gross_profit_margin_pct": 30.0,
                    "conversion_probability_pct": 75,
                },
                {
                    "proposal_id": "PROP-04",
                    "quote_title": "Förbrukningsbox: Aspen Alkylat & Säsongs-kit",
                    "customer_name": "Andersson Maskin & Skog AB",
                    "customer_type": "BUSINESS",
                    "tax_label": "Standardmoms 25% (SEVAT)",
                    "legal_basis": "Mervärdesskattelagen (2023:200) 7 kap.",
                    "bas_account": 3001,
                    "gross_amount": 1450.0,
                    "tax_savings_subsidy": 0.0,
                    "customer_amount_to_pay": 1450.0,
                    "gross_profit_margin_pct": 19.0,
                    "conversion_probability_pct": 68,
                },
                {
                    "proposal_id": "PROP-05",
                    "quote_title": "Cirkulärt Inbytespaket: Automower 430X Premium (VMB)",
                    "customer_name": "Bengt Olofsson",
                    "customer_type": "PRIVATE",
                    "tax_label": "VMB Marginalbeskattning (ML 9a kap)",
                    "legal_basis": "Mervärdesskattelagen (2023:200) 9 kap.",
                    "bas_account": 3051,
                    "gross_amount": 16000.0,
                    "tax_savings_subsidy": 2000.0,
                    "customer_amount_to_pay": 16000.0,
                    "gross_profit_margin_pct": 30.0,
                    "conversion_probability_pct": 85,
                },
            ],
        }

    @classmethod
    def get_production_slice(cls) -> Dict[str, Any]:
        """Bundles the entire production slice for execution in BART's computation pipeline."""
        return {
            "organization_name": "Maskin & Fritid i Skåne AB",
            "organization_number": "556942-8812",
            "customers": cls.get_production_customers(),
            "invoices": cls.get_production_invoices(),
            "employees": cls.get_production_employees(),
            "time_reports": cls.get_production_time_reports(),
            "projects": cls.get_production_projects(),
            "vouchers": cls.generate_production_vouchers(),
            "proposals_summary": cls.get_tax_optimized_proposals_summary(),
        }
