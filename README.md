# Amazon → Tally Converter

Flask app that converts Amazon B2B/B2C invoices (CSV/XLSX) into a Tally-ready Excel workbook with **Sales** and **Sales Return** sheets. GST is split into CGST/SGST or IGST based on Seller State vs State of Supply (from input).  
Run:

```bash
pip install -r requirements.txt
python app.py


---

### Why this matches your spec
- **Single workbook** → “Sales” + “Sales Return (blank)” sheets, plus `_metadata`. :contentReference[oaicite:1]{index=1}  
- **Columns & fixed values**: “Sundry Debtors”, “Sales through Ecommerce”, “Sale through Amazon”, etc., exactly as required. :contentReference[oaicite:2]{index=2}  
- **GST logic**: Uses uploaded **Taxes** value, splits to CGST/SGST for intra-state or IGST for inter-state; **Total Amount = Amount + Taxes**. :contentReference[oaicite:3]{index=3}  
- **Merge B2B + B2C**: Upload both files together; they’re combined before export. :contentReference[oaicite:4]{index=4}  

If you want, I can also add a **CLI test runner** (`python test_run.py <file> <seller_state> amazon`) like before.
