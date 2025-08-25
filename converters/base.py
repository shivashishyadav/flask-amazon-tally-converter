"""
Shared utilities & Tally schema for e-commerce → Tally conversion.
"""

import pandas as pd
from dateutil import parser as dateparser

# Tally output schema (Sales sheet)
TALLY_COLUMNS = [
    "Voucher No",
    "Voucher Date",
    "Customer Name",
    "Group",
    "Address",
    "State",
    "GST Type",
    "GST Number",
    "Sales Ledger Name",
    "Item Name",
    "Batch No.",
    "Expiry",
    "HSN Code",
    "Quantity",
    "Rate",
    "Amount",
    "Taxes",
    "CGST Ledger Name",
    "CGST Amount",
    "SGST Ledger Name",
    "SGST Amount",
    "IGST Ledger Name",
    "IGST Amount",
    "Total Amount",
    "Other Charges Ledger",
    "Other Charges Amount",
]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip spaces; also provide dashed/underscored variants."""
    df = df.copy()
    new_cols = {}
    for c in df.columns:
        base = str(c).strip().lower()
        new_cols[c] = base
    df = df.rename(columns=new_cols)
    return df


def parse_date(val) -> str:
    """Parse to YYYY-MM-DD, else empty."""
    try:
        return dateparser.parse(str(val)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def gst_split_from_tax(taxes: float, seller_state: str, buyer_state: str):
    """
    Split the *Taxes* value based on intra/inter-state rule:
      - same state  -> CGST = Taxes/2, SGST = Taxes/2, IGST = 0
      - different   -> IGST = Taxes, CGST = SGST = 0
    (Matches your spec to base CGST/SGST/IGST on the uploaded tax amount.)
    """
    s = (seller_state or "").strip().lower()
    b = (buyer_state or "").strip().lower()
    intra = bool(s and b and s == b)

    taxes = round(safe_float(taxes, 0.0), 2)
    if intra:
        cgst = round(taxes / 2.0, 2)
        sgst = round(taxes / 2.0, 2)
        igst = 0.0
    else:
        cgst = 0.0
        sgst = 0.0
        igst = taxes
    return cgst, sgst, igst
