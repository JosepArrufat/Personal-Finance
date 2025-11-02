import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from Budget import Budget, BudgetLine
from BudgetManager import BudgetManager
from functions import (
    load_transactions,
    assign_category,
    edit_rows_wrapper,
    initialize_session_state,
    create_df_from_file,
)
from constants import (
    STORE_KEY,
    BUDGETS_KEY,
    CREATING_BUDGET_KEY,
    DF_EXPENSES_KEY,
    DF_INCOME_KEY,
)
from CategoryStore import CategoryStore

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
        st.session_state[CREATING_BUDGET_KEY] = True
    
    if st.session_state.get(CREATING_BUDGET_KEY, False):
        create_budget_form()
    
    manager = st.session_state[BUDGETS_KEY]
    budgets = manager.get_budgets()
    if budgets:
        st.sidebar.subheader("Active Budgets")
        for name, budget in budgets.items():
            with st.sidebar.expander(f"💰 {budget.name}"):
                summary = budget.summary()
                st.write(f"**Period:** {budget.start_date} to {budget.end_date}")
                st.write(f"**Limit:** ${budget.limit:,.2f}")
                st.write(f"**Spent:** ${summary.get('total_spent', 0):,.2f}")
                remaining = budget.limit - summary.get('total_spent', 0)
                st.write(f"**Remaining:** ${remaining:,.2f}")
                
                if st.button("🗑️ Delete", key=f"delete_budget_{name}"):
                    manager.budgets.pop(name, None)
                    manager.delete_budget(name) if hasattr(manager, "delete_budget") else manager.budgets.pop(name, None)
                    st.session_state[BUDGETS_KEY] = manager
                    st.rerun()
    else:
        st.sidebar.info("No budgets created yet. Click 'Create New Budget' to start!")

def create_budget_form():
    st.sidebar.subheader("Create New Budget")
    
    with st.sidebar.form(key="budget_form", clear_on_submit=True):
        name = st.text_input("Budget Name", placeholder="e.g., Monthly Groceries")
        
        categories = st.multiselect(
            "Categories to Track (optional)",
            options=st.session_state[STORE_KEY].data["categories"]
        )
        
        tags = st.multiselect(
            "Include Tags (optional)",
            options=st.session_state[STORE_KEY].tags_list
        )
        
        tags_exclude = st.multiselect(
            "Exclude Tags (optional)",
            options=st.session_state[STORE_KEY].tags_list
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
                if st.session_state[DF_EXPENSES_KEY] is not None:
                    for _, row in st.session_state[DF_EXPENSES_KEY].iterrows():
                        new_budget.add_transaction(row)
                
                if not new_budget.transactions.empty and "tx_id" in new_budget.transactions.columns:
                    new_budget.tx_ids = new_budget.transactions["tx_id"].astype(str).tolist()

                st.session_state[BUDGETS_KEY].add_or_update_budget(new_budget)
                st.session_state[BUDGETS_KEY].save_budget(new_budget)
                st.session_state[CREATING_BUDGET_KEY] = False
                st.success(f"Budget '{name}' created with {len(new_budget.transactions)} transactions!")
                st.rerun()
        
        if cancelled:
            st.session_state[CREATING_BUDGET_KEY] = False


def apply_budgets_to_transactions(df_expenses):
    manager = st.session_state.get(BUDGETS_KEY)
    if manager is None:
        return

    budgets_dict = manager.get_budgets() 
    if not budgets_dict or df_expenses is None or df_expenses.empty:
        return

    budgets = list(budgets_dict.values())
    for b in budgets:
        b.transactions = pd.DataFrame()

    st.subheader("📈 Budget Summary")

    for _, row in df_expenses.iterrows():
        for b in budgets:
            b.add_transaction(row)

    if not budgets:
        return

    cols = st.columns(min(len(budgets), 3))

    for idx, budget in enumerate(budgets):
        summary = budget.summary()
        total_spent = summary.get("total_spent", 0)
        remaining = budget.limit - total_spent
        percentage = (total_spent / budget.limit * 100) if budget.limit > 0 else 0

        with cols[idx % len(cols)]:
            st.metric(
                label=f"💰 {budget.name.upper()}",
                value=f"${total_spent:,.2f} / ${budget.limit:,.2f}",
                delta=f"${remaining:,.2f} remaining",
                delta_color="normal" if remaining >= 0 else "inverse",
            )
            st.caption(f"Total of {len(budget.transactions)} transactions")
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_text = st.text_input(
            "Add new expense category",
            placeholder="e.g., groceries, entertainment...",
            key="category-input"
        )
    
    with col2:
        if st.button("➕ Add Category", key="add_category_button"):
            if category_text:
                st.session_state[STORE_KEY].add_category(
                    name=category_text, 
                    scope="categories"
                )
                st.success(f"Category '{category_text}' added!")
                st.rerun()
        if st.button("💾 Save Changes", key="save_category_changes"):
            st.session_state[STORE_KEY].save_all()
            st.success("Changes saved successfully!")
    df_expenses["tags"] = df_expenses["tags"].apply(
        lambda x: ", ".join(x) if isinstance(x, (list, tuple)) else (x or "")
    )
    df_expenses_edited = st.data_editor(
        df_expenses,
        hide_index=True,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                help="Select Category",
                width="medium",
                options=[k.capitalize() for k in st.session_state[STORE_KEY].get_options(scope="categories")],
                required=True,
            ),
            "tx_id": None,
            "Status": None,
           "tags": st.column_config.TextColumn(
                "Tags",
                help="Enter comma-separated tags (e.g. groceries, food)",
                required=False,
            )
        },
        on_change=edit_rows_wrapper,
        args=(
            "categories",
            df_expenses,
            st.session_state[STORE_KEY],
            "data-editor"
        ),
        key="data-editor",
    )
    
    st.session_state[DF_EXPENSES_KEY] = df_expenses_edited
    
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
                st.session_state[STORE_KEY].add_category(
                    name=category_text,
                    scope="income_categories"
                )
                st.success(f"Category '{category_text}' added!")
                st.rerun()
    with col2:
        if st.button("💾 Save Changes", key="save_income_category_changes"):
            st.session_state[STORE_KEY].save_all()
            st.success("Changes saved successfully!")
            st.session_state[STORE_KEY].load_all()
    
    df_income_edited = st.data_editor(
        df_income,
        hide_index=True,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                help="Select Category",
                width="medium",
                options=[k.capitalize() for k in st.session_state[STORE_KEY].get_options(scope="income_categories")],
                required=True,
            )
        },
        on_change=edit_rows_wrapper,
        args=(
            "income_categories",
            df_income,
            st.session_state[STORE_KEY],
            "income-editor"
        ),
        key="income-editor",
    )
    
    st.session_state[DF_INCOME_KEY] = df_income_edited
    
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
    elif st.session_state.get(DF_EXPENSES_KEY) is not None:
        apply_budgets_to_transactions(st.session_state[DF_EXPENSES_KEY])
        display_transactions(st.session_state[DF_EXPENSES_KEY], st.session_state.get(DF_INCOME_KEY))
    else:
        st.info("👆 Please upload a CSV file to get started")

if __name__ == "__main__":
    main()