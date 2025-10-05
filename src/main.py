import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json


def save_categories(categories_file, category):
    try:
        with open(categories_file, "w") as f:
            json.dump(st.session_state[category], f)
    except IOError as e:
        st.error(f"Error creating {categories_file} file")

def load_categories(categories_file, state):
    if state not in st.session_state:
        st.session_state[state] = {
            "Uncategorized": [],
        }
    if not os.path.exists(categories_file):
        try:
            with open(categories_file, "w") as f:
                json.dump(st.session_state[state], f)
        except IOError as e:
            st.error(f"Error creating {categories_file} file")
    try:
        with open(categories_file, "r") as f:
            st.session_state[state] = json.load(f)
    except IOError as e:
        st.error(f"Error reading {categories_file} file")


def add_categories(new_category, category,categories_file):
    if category == "Uncategorized" or category in st.session_state[category]:
        return
    st.session_state[category][new_category.capitalize()] = []
    try:
        with open(categories_file, "w") as f:
            json.dump(st.session_state[category], f)
    except IOError as e:
        st.error(f"Error creating {categories_file} file")

def assign_category(row, category):
    concept = row["Details"]
    for k, v in st.session_state[category].items():
        if concept in v:
            return k
    return "Uncategorized"
        
def handle_selection(categories_file, category, key, df):
    changes = st.session_state[key]
    edited_rows = changes["edited_rows"]
    for rw_idx, row_changes in edited_rows.items():
        row = st.session_state[df].iloc[rw_idx]
        for k, v in st.session_state[category].items():
            if row["Details"] in v:
                v.remove(row["Details"])
        st.session_state[category][row_changes["Category"]].append(row["Details"])
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

def main():
    st.set_page_config(
        page_title = "Simple Finance Dashboard",
        page_icon = "💰",
        layout = "wide",
    )

    load_categories("categories.json", "categories")
    load_categories("income_categories.json", "income_categories")

    st.title("Finance Manager Dashboard")
    st.markdown("""
    Upload your bank or credit card statement (CSV format) below. 
    We'll clean the data, categorize transactions, and visualize your spending.
    """)
    st.markdown("---")
    st.header("Finance Manager Dashboard")
  
    uploaded_transactions = st.file_uploader(
        "Upload your csv transactions file",
        type=['csv']
    )
    if uploaded_transactions is not None:
        df = load_transactions(uploaded_transactions)
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
                        options=st.session_state.categories.keys(),
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
                        options=st.session_state["income_categories"].keys(),
                        required=True,
                    )
                },
                on_change=handle_selection,
                args=("income_categories.json", "income_categories", "income-editor", "df_income"),
                key="income-editor",
            )
            st.session_state["df_income"] = df_income.copy()
        fig = px.pie(
            df_income,
            values="Amount",
            names="Category",
            title="Income by Category"
    )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please upload a CSV file")
    

if __name__ == "__main__":
    main()