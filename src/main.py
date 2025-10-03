import streamlit as st
import pandas as pd

def load_transactions(file):
    try:
        df = pd.read_csv(file);
        df.colums = [col.strip() for col in df.columns]
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.date
        df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        df["Category"] = "Uncategorized"
        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None
# TODO: add categories for each transaction starting with def, state
def main():
    st.set_page_config(
        page_title = "Simple Finance Dashboard",
        page_icon = "💰",
        layout = "wide",
    )
    st.title("Finance Manager Dashboard")
    st.markdown("""
    Upload your bank or credit card statement (CSV format) below. 
    We'll clean the data, categorize transactions, and visualize your spending.
    """)
    st.markdown("---")
    st.header("Finance Manager Dashboard")
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
        st.write(f"CLICKED: {category_text}")
    uploaded_transactions = st.file_uploader(
        "Upload your csv transactions file",
        type=['csv']
    )
    if uploaded_transactions is not None:
        df = load_transactions(uploaded_transactions)
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Please upload a CSV file")
    

if __name__ == "__main__":
    main()