import io
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
import pandas as pd

from converters import amazon

app = Flask(__name__)
app.secret_key = "dev-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64MB

ALLOWED_EXT = {".csv", ".xlsx", ".xls"}


def _ext(name: str) -> str:
    name = name or ""
    i = name.rfind(".")
    return name[i:].lower() if i >= 0 else ""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        seller_state = (request.form.get("seller_state") or "").strip()
        if not seller_state:
            flash("Select Seller State to split GST properly.", "warning")
            return redirect(url_for("index"))

        if "files" not in request.files:
            flash("No files uploaded.", "danger")
            return redirect(url_for("index"))

        files = request.files.getlist("files")
        parsed = []
        sources = []

        for f in files:
            if not f or f.filename == "":
                continue
            ext = _ext(f.filename)
            if ext not in ALLOWED_EXT:
                flash(f"Skipping {f.filename}: unsupported type {ext}", "warning")
                continue

            try:
                f.stream.seek(0)
                df = (
                    pd.read_csv(f, low_memory=False)
                    if ext == ".csv"
                    else pd.read_excel(f)
                )
            except Exception as e:
                flash(f"Failed to read {f.filename}: {e}", "danger")
                continue

            try:
                out = amazon.convert(df, seller_state)
            except Exception as e:
                flash(f"Amazon conversion failed for {f.filename}: {e}", "danger")
                continue

            if not out.empty:
                parsed.append(out)
                sources.append(f.filename)

        if not parsed:
            flash("No valid rows parsed. Please verify your Amazon files.", "danger")
            return redirect(url_for("index"))

        sales = pd.concat(parsed, ignore_index=True)

        # Sales Return (blank sheet as per spec; user can manually fill later)
        sales_return = sales.head(0).copy()

        # Metadata
        meta = pd.DataFrame(
            {
                "Generated On": [datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
                "Seller State": [seller_state],
                "Sources": [", ".join(sources)],
                "Parser": ["Amazon"],
            }
        )

        # Write in-memory Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as xw:
            sales.to_excel(xw, sheet_name="Sales", index=False)
            sales_return.to_excel(xw, sheet_name="Sales Return", index=False)
            meta.to_excel(xw, sheet_name="_metadata", index=False)
        output.seek(0)

        fname = f"tally_amazon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(
            output,
            as_attachment=True,
            download_name=fname,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return render_template("index.html")


@app.route("/healthz")
def healthz():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
