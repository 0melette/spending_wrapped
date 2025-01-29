import uuid
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "meow"

# In-memory store for transactions (temporary)
transactions_db = []


@app.route("/")
def index():
    total_amount = sum(t["amount"] for t in transactions_db)
    total_transactions = len(transactions_db)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    min_amount = request.args.get("min_amount", type=float)
    max_amount = request.args.get("max_amount", type=float)

    # Apply filters
    filtered_transactions = transactions_db
    if start_date:
        filtered_transactions = [t for t in filtered_transactions if t["date"] >= start_date]
    if end_date:
        filtered_transactions = [t for t in filtered_transactions if t["date"] <= end_date]
    if min_amount is not None:
        filtered_transactions = [t for t in filtered_transactions if t["amount"] >= min_amount]
    if max_amount is not None:
        filtered_transactions = [t for t in filtered_transactions if t["amount"] <= max_amount]

    # Get pagination parameters
    page = int(request.args.get("page", 1))
    per_page = 20 
    start = (page - 1) * per_page
    end = start + per_page

    # Calculate total pages
    total_pages = (len(filtered_transactions) + per_page - 1) // per_page  # Ceiling division

    return render_template(
        "index.html",
        total_amount=total_amount,
        total_transactions=total_transactions,
        transactions=filtered_transactions[start:end],
        page=page,
        total_pages=total_pages
    )


@app.route("/upload", methods=["GET", "POST"])
def upload_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            try:
                df = pd.read_csv(file, encoding="utf-8")

                print("Detected Columns:", df.columns.tolist())

                required_cols = ["Date", "Transaction", "Amount"]
                for col in required_cols:
                    if col not in df.columns:
                        flash(f"Missing required column: {col}", "error")
                        return redirect(request.url)

                if "Tags/Notes" not in df.columns:
                    df["Tags/Notes"] = ""

                for _, row in df.iterrows():
                    transaction_id = str(uuid.uuid4())
                    transaction = {
                        "id": transaction_id,
                        "date": str(row["Date"]),
                        "description": str(row["Transaction"]),
                        "amount": float(row["Amount"]),
                        "tags_notes": str(row["Tags/Notes"]),
                    }
                    transactions_db.append(transaction)

                flash("File uploaded and processed successfully!", "success")
                return redirect(url_for("index"))
            except Exception as e:
                flash(f"Error parsing CSV: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Please upload a valid CSV file.", "error")
            return redirect(request.url)

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
