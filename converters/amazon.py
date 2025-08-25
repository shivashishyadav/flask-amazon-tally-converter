"""
Amazon B2B & B2C → Tally Sales rows (merged)
Column picks are tolerant to multiple header variants from Amazon.
"""

import pandas as pd
from .base import TALLY_COLUMNS, normalize, parse_date, safe_float, gst_split_from_tax

FIXED_GROUP = "Sundry Debtors"
FIXED_SALES_LEDGER = "Sales through Ecommerce"
FIXED_CUSTOMER = "Sale through Amazon"
LEDGER_CGST = "Output CGST"
LEDGER_SGST = "Output SGST"
LEDGER_IGST = "Output IGST"


def _pick(row, *cands, default=""):
    for c in cands:
        if c in row and pd.notna(row[c]):
            val = row[c]
            if str(val).strip() != "":
                return val
    return default


def _is_b2b(row) -> bool:
    gst = _pick(
        row, "buyer-gstin", "buyer_gstin", "gstin", "buyer gstin", "customer gstin"
    )
    return bool(str(gst).strip())


def convert(df: pd.DataFrame, seller_state: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TALLY_COLUMNS)

    df = normalize(df)

    rows = []
    for _, r in df.iterrows():
        # Voucher
        voucher_no = (
            _pick(
                r,
                "invoice-id",
                "invoice id",
                "invoice_number",
                "invoice number",
                "order-id",
                "order id",
            )
            or "AMZ"
        )
        voucher_date = parse_date(
            _pick(r, "invoice-date", "invoice date", "order-date", "order date")
        )

        # Buyer + state-of-supply
        buyer_state = str(
            _pick(
                r,
                "state of supply",
                "ship-state",
                "ship state",
                "shipping state",
                "destination state",
            )
        ).strip()
        customer_name = FIXED_CUSTOMER

        # GST fields
        is_b2b = _is_b2b(r)
        gst_type = "Registered" if is_b2b else "Unregistered"
        gst_number = (
            _pick(
                r,
                "buyer-gstin",
                "buyer_gstin",
                "gstin",
                "buyer gstin",
                "customer gstin",
            )
            if is_b2b
            else ""
        )

        # Item line
        item = _pick(
            r, "product-name", "product name", "item name", "sku", default="Item"
        )
        hsn = _pick(r, "hsn", "hsn code")
        qty = safe_float(_pick(r, "quantity", "qty", default=1), 1)
        rate = safe_float(
            _pick(r, "unit-price", "unit price", "price", "rate", default=0), 0
        )
        amount = safe_float(
            _pick(r, "taxable-value", "taxable value", "amount", default=qty * rate), 0
        )

        # Taxes from source (spec wants to take Taxes from uploaded file)
        taxes = safe_float(
            _pick(
                r,
                "tax-amount",
                "tax amount",
                "gst-amount",
                "gst amount",
                "tax",
                default=0,
            ),
            0,
        )

        # GST split based on seller vs buyer state
        cgst_amt, sgst_amt, igst_amt = gst_split_from_tax(
            taxes, seller_state, buyer_state
        )

        # Build Tally row
        rows.append(
            {
                "Voucher No": voucher_no,
                "Voucher Date": voucher_date,
                "Customer Name": customer_name,
                "Group": FIXED_GROUP,
                "Address": buyer_state,  # Address = State of Supply (spec)
                "State": buyer_state,
                "GST Type": gst_type,
                "GST Number": gst_number,
                "Sales Ledger Name": FIXED_SALES_LEDGER,
                "Item Name": item,
                "Batch No.": "",
                "Expiry": "",
                "HSN Code": hsn,
                "Quantity": qty,
                "Rate": rate,
                "Amount": amount,
                "Taxes": taxes,
                "CGST Ledger Name": LEDGER_CGST,
                "CGST Amount": cgst_amt,
                "SGST Ledger Name": LEDGER_SGST,
                "SGST Amount": sgst_amt,
                "IGST Ledger Name": LEDGER_IGST,
                "IGST Amount": igst_amt,
                "Total Amount": round(amount + taxes, 2),  # Amount + Taxes (spec)
                "Other Charges Ledger": "",
                "Other Charges Amount": "",
            }
        )

    return pd.DataFrame(rows, columns=TALLY_COLUMNS)
