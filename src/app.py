import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
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

def main():
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
  
    uploaded_transactions = st.file_uploader(
        "Upload your csv transactions file",
        type=['csv']
    )
    if uploaded_transactions is not None:
        df = load_transactions(uploaded_transactions)
        df_expenses = df[df["Debit/Credit"] == "Debit"].copy()
        df_expenses["Category"] = df.apply(assign_category, axis=1, args=("categories", st.session_state["store"].is_loaded()))
        df_income = df[df["Debit/Credit"] == "Credit"].copy()
        df_income["Category"] = df.apply(assign_category, axis=1, args=("income_categories", st.session_state["store"].is_loaded()))
        
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
                st.session_state["store"].add_category(name=category_text, scope="categories")
                category_text = ""
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
                    )
                },
                on_change=edit_rows_wrapper,
                args=(
                    "categories",  
                    df_expenses,
                    st.session_state["store"],
                ),
                key="data-editor",
            )
            
            # st.session_state["df_expenses"] = df_expenses.copy()
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
                st.session_state["store"].add_category(name=category_text,scope="income_categories")
                category_text = ""

            save_i_button = st.button(
                "Save changes", 
                key="save_category_changes"
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
                    st.session_state["store"]
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
    else:
        st.info("Please upload a CSV file")
    

if __name__ == "__main__":
    main()