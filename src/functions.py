import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from constants import(
    EXPENSES_CATEGORY,
    INCOME_CATEGORY
)

#TODO: Clean with function files, handle bank formats, custom data range, undo, validators?, RULES?

def save_categories(categories_file, category):
    try:
        with open(categories_file, "w") as f:
            json.dump(st.session_state[category.lower()], f)
    except IOError as e:
        st.error(f"Error creating {categories_file} file: {e}")

def load_categories(categories_file, state):
    state = state.lower()
    loaded_flag = state + "_loaded"
    if not st.session_state.get(loaded_flag, False):
        if state not in st.session_state:
            st.session_state[state] = {
                "uncategorized": [],
            }
        if not os.path.exists(categories_file):
            try:
                with open(categories_file, "w") as f:
                    json.dump(st.session_state[state], f)
            except IOError as e:
                st.error(f"Error creating {categories_file} file: {e}")
        try:
            with open(categories_file, "r") as f:
                loaded_data = json.load(f)
                st.session_state[state] = {k.lower(): [d.lower() for d in v] for k, v in loaded_data.items()}
                st.session_state[loaded_flag] = True
        except IOError as e:
            st.error(f"Error reading {categories_file} file: {e}")

def add_categories(new_category, category,categories_file):
    category = category.lower()
    new_category = new_category.lower()
    if new_category == "uncategorized" or new_category in st.session_state[category]:
        return
    st.session_state[category][new_category] = []
    try:
        with open(categories_file, "w") as f:
            json.dump(st.session_state[category], f)
    except IOError as e:
        st.error(f"Error creating {categories_file} file: {e}")

def assign_category(row, category, is_loaded):
    if is_loaded:
        concept = row["Details"].lower()
        category = category.lower()
        lookup = st.session_state["store"].get_lookup(category) 
        k = lookup.get(concept)
        if k:
            return k.capitalize()
        return "Uncategorized"
        
def handle_selection(categories_file, category, key, df):
    category = category.lower()
    changes = st.session_state[key]
    edited_rows = changes["edited_rows"]
    for rw_idx, row_changes in edited_rows.items():
        row = st.session_state[df].iloc[rw_idx]
        detail = row["Details"].lower()
        new_category = row_changes["Category"].lower()
        lookup = st.session_state["details_to_category"] if category == "categories" else st.session_state["details_to_income_category"]
        if detail in lookup:
            old_category = lookup[detail]
            if detail in st.session_state[category][old_category]:
                st.session_state[category][old_category].remove(detail)
            del lookup[detail]
        if new_category not in st.session_state[category]:
            st.session_state[category][new_category] = []
        lookup[detail] = new_category
        st.session_state[category][new_category].append(detail)
    save_categories(categories_file, category)
    
def load_transactions(file):
    try:
        df = pd.read_csv(file);
        df.columns = [col.strip() for col in df.columns]
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.date
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

def load_page():
    load_categories("categories.json", "categories")
    load_categories("income_categories.json", "income_categories")

def edit_rows_wrapper(scope, current_df, store):
    key = "data-editor"
    e_row = "edited_rows"
    edited_data = st.session_state[key][e_row]
    if edited_data:
        store.apply_edits(
            edited_rows=edited_data,
            scope=scope,
            current_df=current_df
        )

def load_dataframes(uploaded_transacrtions):
    df = load_transactions(uploaded_transacrtions)
    df_expenses = df[df["Debit/Credit"] == "Debit"].copy()
    df_expenses["Category"] = df.apply(assign_category, axis=1, args=("categories",))
    df_income = df[df["Debit/Credit"] == "Credit"].copy()
    df_income["Category"] = df.apply(assign_category, axis=1, args=("income_categories",))
    
    tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
    with tab1:
        category_text = st.text_input(
            "Add new transaction category",
            placeholder="Add groceries, videogames, dinning..",
            key="category-input"
            )
        category_button = st.button(
            "Add category", 
            key="add_category_button"
            )
        if category_text and category_button:
            add_categories(category_text, "categories", "categories.json")
        df_expenses = st.data_editor(
            df_expenses,
            hide_index=True,
            column_config = {
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Select Category",
                    width="medium",
                    options=[k.capitalize() for k in st.session_state.categories.keys()],
                    required=True,
                )
            },
            on_change=handle_selection,
            args=("categories.json", "categories", "data-editor", "df_expenses"),
            key="data-editor",
        )
        st.session_state["df_expenses"] = df_expenses.copy()
        fig = px.pie(
            df_expenses,
            values="Amount",
            names="Category",
            title="Expenses by Category"
    )
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        category_text = st.text_input(
            "Add new income category",
            placeholder="Add job, investment, debts..",
            key="category_income-input"
            )
        category_button = st.button(
            "Add category", 
            key="add_income_category_button"
            )
        if category_text and category_button:
            add_categories(category_text,"income_categories","income_categories.json")
        df_income = st.data_editor(
            df_income,
            hide_index=True,
            column_config = {
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Select Category",
                    width="medium",
                    options=[k.capitalize() for k in st.session_state["income_categories"].keys()],
                    required=True,
                )
            },
            on_change=handle_selection,
            args=("income_categories.json", "income_categories", "income-editor", "df_income"),
            key="income-editor",
        )
        st.session_state["df_income"] = df_income.copy()
        fig_income = px.pie(
            df_income,
            values="Amount",
            names="Category",
            title="Income by Category"
            )
        st.plotly_chart(fig_income, use_container_width=True)