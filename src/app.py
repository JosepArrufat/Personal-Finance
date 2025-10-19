import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from Budget import Budget, BudgetLine
from constants import(
    EXPENSES_CATEGORY,
    INCOME_CATEGORY
)
from functions import (
    load_transactions,
    assign_category,
    edit_rows_wrapper,
)
from CategoryStore import CategoryStore

#TODO: Clean with function files, handle bank formats, custom data range, undo, validators?, RULES?
def load_page():
    st.set_page_config(
        page_title = "Simple Finance Dashboard",
        page_icon = "💰",
        layout = "wide",
    )
    store = CategoryStore(
        categories_path="categories.json", 
        income_categories_path="income_categories.json"
        )
    if not "store" in st.session_state:
        st.session_state["store"] = store
        st.session_state["store"].load_all()
    
    st.title("Finance Manager Dashboard")
    st.markdown("""
    Upload your bank or credit card statement (CSV format) below. 
    We'll clean the data, categorize transactions, and visualize your spending.
    """)
    st.markdown("---")
    st.header("Personal Finance Manager")

def create_df_from_file(uploaded_transactions):
    df = load_transactions(uploaded_transactions)
    df = df.drop(columns=["Status"], axis=1)
    df_expenses = df[df["Debit/Credit"] == "Debit"].copy()
    df_expenses["Category"] = df.apply(assign_category, axis=1, args=("categories", st.session_state["store"].is_loaded()))
    file_name = uploaded_transactions.name
    df_expenses = st.session_state["store"].apply_tags_to_df(df=df_expenses, filename=file_name)
    df_income = df[df["Debit/Credit"] == "Credit"].copy()
    df_income["Category"] = df.apply(assign_category, axis=1, args=("income_categories", st.session_state["store"].is_loaded()))
    
    tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
    with tab1:
        category_text = st.text_input(
            "Add new transaction category",
            placeholder="Add groceries, videogames, dinning..",
            key="category-input"
            )
        col1_e, col2_e, col3_e = st.columns(3)
        with col1_e:
            category_button = st.button(
                "Add category", 
                key="add_category_button"
            )
            if category_text and category_button:
                st.session_state["store"].add_category(name=category_text, scope="categories")
                category_text = ""
        with col2_e:
            budget_button = st.button(
                "Create budget", 
                key="create_budget_button"
            )
            if budget_button:
                st.session_state["Add budget"] = True
            if st.session_state.get("Add budget", False):
                with st.form(key="budget_form"):
                    name = st.text_input("New budget name")
                    categories = st.multiselect("Add categories", options=st.session_state["store"].data["categories"])
                    tags = st.multiselect("Add tags", options=st.session_state["store"].tags_list)
                    tags_exclude = st.multiselect("Exclude tags", options=st.session_state["store"].tags_list)
                    budget_limit = st.number_input("Add budget limit")
                    start_date = st.date_input(
                        "Start Date",
                        min_value=date(2025, 1, 1),
                        max_value=date(2030, 12, 31),
                        value=date(2025, 1, 1)
                        )
                    end_date = st.date_input(
                        "End Date",
                        min_value=date(2025, 1, 1),
                        max_value=date(2030, 12, 31),
                        value=date(2030, 12, 31)
                        )
                    submitted = st.form_submit_button("Submit")
                    if submitted:
                        print("is this shit running")
                        new_budget = Budget(
                            name=name, 
                            start_date=start_date, 
                            end_date=end_date,
                            limit=budget_limit
                            )
                        for category in categories:
                            new_budget.add_line(BudgetLine(category=category)) 
                        if tags:
                            new_budget.add_line(BudgetLine(include_tags=tags))
                        if tags_exclude:
                            new_budget.add_line(BudgetLine(exclude_tags=tags))
                        
                        print(new_budget.transactions)
                        print(new_budget.summary())
                        st.session_state["Add budget"] = False
                    
        with col3_e:
            save_button = st.button(
                "Save changes", 
                key="save_category_changes"
            )
            if save_button:
                st.session_state["store"].save_all()
        
        df_expenses = st.data_editor(
            df_expenses,
            hide_index=True,
            column_config = {
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Select Category",
                    width="medium",
                    options=[k.capitalize() for k in st.session_state["store"].get_options(scope="categories")],
                    required=True,
                ),
                "transaction_id": None,
                "tags": st.column_config.MultiselectColumn(
                    "tags",
                    help="Select multiple tags (type to search)",
                    options=st.session_state["store"].tags_list,
                    required=False
                )
            },
            on_change=edit_rows_wrapper,
            args=(
                "categories",  
                df_expenses,
                st.session_state["store"],
                "data-editor"
            ),
            key="data-editor",
        )
        
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
        col1, col2 = st.columns(2)
        with col1:
            category_button = st.button(
                "Add category", 
                key="add_income_category_button"
            )
            if category_text and category_button:
                st.session_state["store"].add_category(name=category_text,scope="income_categories")
                category_text = ""
        with col2:
            save_i_button = st.button(
                "Save changes in dataframe", 
                key="save_income_category_changes"
            )
            if save_i_button:
                st.session_state["store"].save_all()

        df_income = st.data_editor(
            df_income,
            hide_index=True,
            column_config = {
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Select Category",
                    width="medium",
                    options=[k.capitalize() for k in st.session_state["store"].get_options(scope="income_categories")],
                    required=True,
                )
            },
            on_change=edit_rows_wrapper,
            args=(
                "income_categories", 
                df_income,
                st.session_state["store"],
                "income-editor"
                ),
            key="income-editor",
        )
        # st.session_state["df_income"] = df_income.copy()
        fig_income = px.pie(
            df_income,
            values="Amount",
            names="Category",
            title="Income by Category"
            )
        st.plotly_chart(fig_income, use_container_width=True)

def main():
    load_page()
    uploaded_transactions = st.file_uploader(
        "Upload your csv transactions file",
        type=['csv']
    )
    if uploaded_transactions is not None:
        create_df_from_file(uploaded_transactions)
    else:
        st.info("Please upload a CSV file")
    

if __name__ == "__main__":
    main()