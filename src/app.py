import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
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

def initialize_session_state():
    if "store" not in st.session_state:
        store = CategoryStore(
            categories_path="categories.json", 
            income_categories_path="income_categories.json"
        )
        st.session_state["store"] = store
        st.session_state["store"].load_all()
    if "budgets" not in st.session_state:
        st.session_state["budgets"] = []
    if "creating_budget" not in st.session_state:
        st.session_state["creating_budget"] = False
    if "df_expenses" not in st.session_state:
        st.session_state["df_expenses"] = None
    if "df_income" not in st.session_state:
        st.session_state["df_income"] = None

def load_page():
    st.set_page_config(
        page_title="Simple Finance Dashboard",
        page_icon="💰",
        layout="wide",
    )
    
    st.title("Finance Manager Dashboard")
    st.markdown("""
    Upload your bank or credit card statement (CSV format) below. 
    We'll clean the data, categorize transactions, and visualize your spending.
    """)
    st.markdown("---")

def manage_budgets_sidebar():
    st.sidebar.header("📊 Budget Management")
    
    if st.sidebar.button("➕ Create New Budget", use_container_width=True):
        st.session_state["creating_budget"] = True
    
    if st.session_state.get("creating_budget", False):
        create_budget_form()
    
    if st.session_state["budgets"]:
        st.sidebar.subheader("Active Budgets")
        for idx, budget in enumerate(st.session_state["budgets"]):
            with st.sidebar.expander(f"💰 {budget.name}"):
                summary = budget.summary()
                st.write(f"**Period:** {budget.start_date} to {budget.end_date}")
                st.write(f"**Limit:** ${budget.limit:,.2f}")
                st.write(f"**Spent:** ${summary.get('total_spent', 0):,.2f}")
                st.write(f"**Transactions:** {len(budget.transactions)}")
                remaining = budget.limit - summary.get('total_spent', 0)
                st.write(f"**Remaining:** ${remaining:,.2f}")
                
                if st.button("🗑️ Delete", key=f"delete_budget_{idx}"):
                    st.session_state["budgets"].pop(idx)
                    st.rerun()
    else:
        st.sidebar.info("No budgets created yet. Click 'Create New Budget' to start!")

def create_budget_form():
    st.sidebar.subheader("Create New Budget")
    
    with st.sidebar.form(key="budget_form", clear_on_submit=True):
        name = st.text_input("Budget Name", placeholder="e.g., Monthly Groceries")
        
        categories = st.multiselect(
            "Categories to Track (otional)",
            options=st.session_state["store"].data["categories"]
        )
        
        tags = st.multiselect(
            "Include Tags (optional)",
            options=st.session_state["store"].tags_list
        )
        
        tags_exclude = st.multiselect(
            "Exclude Tags (optional)",
            options=st.session_state["store"].tags_list
        )
        
        budget_limit = st.number_input(
            "Budget Limit ($)",
            min_value=0.0,
            value=1000.0,
            step=100.0
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                min_value=date(2023, 1, 1),
                max_value=date(2030, 12, 31),
                value=date(2025, 1, 1)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                min_value=date(2025, 1, 1),
                max_value=date(2030, 12, 31),
                value=date(2025, 12, 31)
            )
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("✅ Create", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("Please enter a budget name")
            else:
                new_budget = Budget(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    limit=budget_limit,
                )
                if categories:
                    for category in categories:
                        new_budget.add_line(BudgetLine(
                            category=category.lower(),
                            include_tags=tuple(tags) if tags else (),
                            exclude_tags=tuple(tags_exclude) if tags_exclude else (),
                        ))
                else:
                    new_budget.add_line(BudgetLine(
                            include_tags=tuple(tags) if tags else (),
                            exclude_tags=tuple(tags_exclude) if tags_exclude else (),
                        ))
                if st.session_state["df_expenses"] is not None:
                    for _, row in st.session_state["df_expenses"].iterrows():
                        new_budget.add_transaction(row)
                
                st.session_state["budgets"].append(new_budget)
                st.session_state["creating_budget"] = False
                st.success(f"Budget '{name}' created with {len(new_budget.transactions)} transactions!")
                st.rerun()
        
        if cancelled:
            st.session_state["creating_budget"] = False

def create_df_from_file(uploaded_transactions):
    df = load_transactions(uploaded_transactions)
    df = df.drop(columns=["Status"], axis=1)
    
    df_expenses = df[df["Debit/Credit"] == "Debit"].copy()
    df_expenses["Category"] = df.apply(
        assign_category, 
        axis=1, 
        args=("categories", st.session_state["store"].is_loaded())
    )
    file_name = uploaded_transactions.name
    df_expenses = st.session_state["store"].apply_tags_to_df(
        df=df_expenses, 
        filename=file_name
    )
    
    df_income = df[df["Debit/Credit"] == "Credit"].copy()
    df_income["Category"] = df.apply(
        assign_category, 
        axis=1, 
        args=("income_categories", st.session_state["store"].is_loaded())
    )
    
    st.session_state["df_expenses"] = df_expenses
    st.session_state["df_income"] = df_income
    
    return df_expenses, df_income

def apply_budgets_to_transactions(df_expenses):
    if not st.session_state["budgets"] or df_expenses is None or df_expenses.empty:
        return
    
    st.subheader("📈 Budget Summary")
    
    for budget in st.session_state["budgets"]:
        budget.transactions = pd.DataFrame()
        
        for _, row in df_expenses.iterrows():
            budget.add_transaction(row)
    
    cols = st.columns(min(len(st.session_state["budgets"]), 3))
    
    for idx, budget in enumerate(st.session_state["budgets"]):
        summary = budget.summary()
        total_spent = summary.get('total_spent', 0)
        remaining = budget.limit - total_spent
        percentage = (total_spent / budget.limit * 100) if budget.limit > 0 else 0
        
        with cols[idx % 3]:
            st.metric(
                label=f"💰 {budget.name}",
                value=f"${total_spent:,.2f} / ${budget.limit:,.2f}",
                delta=f"${remaining:,.2f} remaining",
                delta_color="normal" if remaining >= 0 else "inverse"
            )
            
            if percentage <= 75:
                bar_color = "🟢"
            elif percentage <= 90:
                bar_color = "🟡"
            else:
                bar_color = "🔴"
            
            st.progress(min(percentage / 100, 1.0))
            st.caption(f"{bar_color} {percentage:.1f}% used ({len(budget.transactions)} transactions)")

def display_expenses_tab(df_expenses):
    st.subheader("💳 Expense Transactions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_text = st.text_input(
            "Add new expense category",
            placeholder="e.g., groceries, entertainment...",
            key="category-input"
        )
        if st.button("➕ Add Category", key="add_category_button"):
            if category_text:
                st.session_state["store"].add_category(
                    name=category_text, 
                    scope="categories"
                )
                st.success(f"Category '{category_text}' added!")
                st.rerun()
    
    with col3:
        if st.button("💾 Save Changes", key="save_category_changes"):
            st.session_state["store"].save_all()
            st.success("Changes saved successfully!")
    
    df_expenses_edited = st.data_editor(
        df_expenses,
        hide_index=True,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                help="Select Category",
                width="medium",
                options=[k.capitalize() for k in st.session_state["store"].get_options(scope="categories")],
                required=True,
            ),
            "transaction_id": None,
            "tags": st.column_config.MultiselectColumn(
                "Tags",
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
    
    st.session_state["df_expenses"] = df_expenses_edited
    
    if not df_expenses_edited.empty:
        fig = px.pie(
            df_expenses_edited,
            values="Amount",
            names="Category",
            title="Expenses by Category",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)

def display_income_tab(df_income):
    st.subheader("💵 Income Transactions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_text = st.text_input(
            "Add new income category",
            placeholder="e.g., salary, investment...",
            key="category_income-input"
        )
        if st.button("➕ Add Category", key="add_income_category_button"):
            if category_text:
                st.session_state["store"].add_category(
                    name=category_text,
                    scope="income_categories"
                )
                st.success(f"Category '{category_text}' added!")
                st.rerun()
    
    with col2:
        if st.button("💾 Save Changes", key="save_income_category_changes"):
            st.session_state["store"].save_all()
            st.success("Changes saved successfully!")
    
    df_income_edited = st.data_editor(
        df_income,
        hide_index=True,
        column_config={
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
    
    st.session_state["df_income"] = df_income_edited
    
    if not df_income_edited.empty:
        fig_income = px.pie(
            df_income_edited,
            values="Amount",
            names="Category",
            title="Income by Category",
            hole=0.3
        )
        st.plotly_chart(fig_income, use_container_width=True)

def display_transactions(df_expenses, df_income):
    st.header("📊 Transactions")
    
    tab1, tab2 = st.tabs(["💳 Expenses (Debits)", "💵 Income (Credits)"])
    
    with tab1:
        display_expenses_tab(df_expenses)
    
    with tab2:
        display_income_tab(df_income)

def main():
    load_page()
    initialize_session_state()
    manage_budgets_sidebar()  
    uploaded_transactions = st.file_uploader(
        "📁 Upload your CSV transactions file",
        type=['csv']
    )
    if uploaded_transactions is not None:
        df_expenses, df_income = create_df_from_file(uploaded_transactions)
        apply_budgets_to_transactions(df_expenses)
        display_transactions(df_expenses, df_income)
    elif st.session_state["df_expenses"] is not None:
        apply_budgets_to_transactions(st.session_state["df_expenses"])
        display_transactions(st.session_state["df_expenses"], st.session_state["df_income"])
    else:
        st.info("👆 Please upload a CSV file to get started")

if __name__ == "__main__":
    main()