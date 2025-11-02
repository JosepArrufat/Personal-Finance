import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
from constants import(
    EXPENSES_CATEGORY,
    INCOME_CATEGORY,
    STORE_KEY,
    BUDGETS_KEY,
    DF_EXPENSES_KEY,
    DF_INCOME_KEY,
    CREATING_BUDGET_KEY,
    SESSION_DEFAULTS,
)
from CategoryStore import CategoryStore
from BudgetManager import BudgetManager


def initialize_session_state():
    for k, default in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = default
    if st.session_state.get(STORE_KEY) is None:
        store = CategoryStore(
            categories_path="categories.json",
            income_categories_path="income_categories.json",
        )
        store.load_all()
        st.session_state[STORE_KEY] = store

    if st.session_state.get(BUDGETS_KEY) is None:
        mgr = BudgetManager()
        mgr.load_all()
        st.session_state[BUDGETS_KEY] = mgr


def create_df_from_file(uploaded_transactions):
    df = load_transactions(uploaded_transactions)
    if df is None:
        return None, None

    df_expenses = df[df.get("Debit/Credit") == "Debit"].copy()
    df_expenses["Category"] = df.apply(assign_category, axis=1, args=("categories", st.session_state[STORE_KEY].is_loaded()))
    file_name = getattr(uploaded_transactions, "name", "uploaded.csv")
    df_expenses = st.session_state[STORE_KEY].apply_tags_to_df(df=df_expenses, filename=file_name)

    df_income = df[df.get("Debit/Credit") == "Credit"].copy()
    df_income["Category"] = df.apply(assign_category, axis=1, args=("income_categories", st.session_state[STORE_KEY].is_loaded()))

    return df_expenses, df_income

def assign_category(row, category, is_loaded):
    if is_loaded:
        concept = row["Details"].lower()
        category = category.lower()
        lookup = st.session_state[STORE_KEY].get_lookup(category)
        k = lookup.get(concept)
        if k:
            return k.capitalize()
        return "Uncategorized"
        
def load_transactions(file):
    try:
        df = pd.read_csv(file);
        df.columns = [col.strip() for col in df.columns]
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.date
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        def _make_tx_id(r):
            date_part = r.get("Date")
            amount_part = r.get("Amount")
            details_part = r.get("Details") if "Details" in r.index else ""
            s = f"{date_part!s}|{amount_part!s}|{details_part!s}"
            return hashlib.sha1(s.encode("utf-8")).hexdigest()
        try:
            df = df.reset_index(drop=True)
            df["tx_id"] = df.apply(_make_tx_id, axis=1)
        except Exception:
            df["tx_id"] = [str(i) for i in range(len(df))]

        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

def edit_rows_wrapper(scope, current_df, store, key):
    e_row = "edited_rows"
    edited_data = st.session_state[key][e_row]
    if edited_data:
        store.apply_edits(
            edited_rows=edited_data,
            scope=scope,
            current_df=current_df
        )
        if store.current_file:
            store.apply_tag_edits(edited_rows=edited_data, current_df=current_df)
    

