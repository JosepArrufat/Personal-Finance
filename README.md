Personal Finance — Simple budgeting and transaction categorization

A lightweight Streamlit app to import CSV bank/credit-card statements, automatically categorize transactions (with a persisting tag store), and track budgets safely by storing transaction IDs (not raw DataFrames).

Quick start

1. Create and activate a Python 3.12+ virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install runtime dependencies (Streamlit, pandas, plotly).

```bash
python -m pip install -r requirements.txt
# if no requirements.txt, at minimum:
python -m pip install streamlit pandas plotly
```

3. Run the app

```bash
streamlit run src/app.py
```

Testing

Run unit tests with:

```bash
python -m unittest discover -v
```

Files and configuration

- `src/app.py` — Streamlit UI (keeps rendering and user interactions).
- `src/functions.py` — non-UI helpers (CSV parsing, session initialization, tx_id generation).
- `src/CategoryStore.py` — tag/category persistence (uses `categories.json`, `income_categories.json`, `tags.json`).
- `src/Budget.py`, `src/BudgetManager.py` — budgets persisted to `budgets.json` (stores `tx_ids` rather than DataFrames).
- `src/constants.py` — canonical session-state keys and defaults.

CSV input expectations

- The CSV should include at least: `Date`, `Details`, `Amount`, `Debit/Credit` columns. Date format the app expects is `DD Mon YYYY` (e.g., `01 Jan 2025`) for uploads.

Notes

- Budgets persist only transaction IDs (tx_id) to avoid serializing DataFrames; the code computes deterministic tx_ids from Date|Amount|Details.
- If you modify category/tag files, use the app's "Save Changes" buttons to persist edits.

Future Implementations

- Add compatibility with different bank csv formats, persist df and create new ones from budgets.

