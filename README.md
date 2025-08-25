# Amazon → Tally Converter

Flask app that converts Amazon B2B/B2C invoices (CSV/XLSX) into a Tally-ready Excel workbook with **Sales** and **Sales Return** sheets. GST is split into CGST/SGST or IGST based on Seller State vs State of Supply (from input).  
Run:

```bash
pip install -r requirements.txt
python app.py