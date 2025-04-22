import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import bleach
from passlib.hash import pbkdf2_sha256
import statsmodels.api as sm
import folium
from streamlit_folium import st_folium
import os

# --- File Path ---
CSV_FILE_PATH = r"D:\Projects\Chocolate\Chocolate Sales.csv"

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'role' not in st.session_state:
    st.session_state.role = ''
if 'data' not in st.session_state:
    st.session_state.data = None
if 'users_db' not in st.session_state:
    st.session_state.users_db = None

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    # Create sales table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_person TEXT,
            country TEXT,
            product TEXT,
            date TEXT,
            amount REAL,
            boxes_shipped INTEGER,
            sale_type TEXT
        )
    ''')
    # Create users table
    # Note: The role field in the users table drives access control, restricting Sales Reps to their own data and allowing Owners to manage all records.
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    return conn

# --- User Authentication ---
def authenticate_user(username, password, conn):
    username = bleach.clean(username)
    c = conn.cursor()
    c.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    if result and pbkdf2_sha256.verify(password, result[0]):
        return True, result[1]
    return False, None

def add_user(username, password, role, conn):
    username = bleach.clean(username)
    hashed_password = pbkdf2_sha256.hash(password)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                 (username, hashed_password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# --- Data Loading and Cleaning ---
@st.cache_data
def load_data():
    # Load from CSV
    df = pd.read_csv(CSV_FILE_PATH)
    # Clean data
    df['Amount'] = df['Amount'].replace({'\$': '', ',': '', ' ': ''}, regex=True).astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y').dt.strftime('%Y-%m-%d')
    # Apply sale type classification
    df['sale_type'] = df.apply(
        lambda row: 'Wholesale' if row['Boxes Shipped'] > 100 or row['Amount'] > 5000 else 'Retail',
        axis=1
    )
    # Rename columns for consistency
    df = df.rename(columns={'Sales Person': 'sales_person', 'Country': 'country', 'Product': 'product', 
                            'Date': 'date', 'Amount': 'amount', 'Boxes Shipped': 'boxes_shipped'})
    # Save to database
    conn = sqlite3.connect('sales_data.db')
    df.to_sql('sales', conn, if_exists='replace', index=False)
    conn.close()
    return df

# --- Load Data from Database ---
def load_data_from_db():
    conn = sqlite3.connect('sales_data.db')
    df = pd.read_sql_query('SELECT * FROM sales', conn)
    conn.close()
    return df

# --- Forecasting Function ---
def forecast_sales(df, column='amount', periods=6):
    df['date'] = pd.to_datetime(df['date'])
    monthly = df.groupby(df['date'].dt.to_period('M'))[column].sum().reset_index()
    monthly['date'] = monthly['date'].dt.to_timestamp()
    model = sm.tsa.ExponentialSmoothing(monthly[column], trend='add', seasonal=None).fit()
    forecast = model.forecast(periods)
    forecast_dates = pd.date_range(start=monthly['date'].max() + pd.offsets.MonthBegin(1), 
                                  periods=periods, freq='MS')
    forecast_df = pd.DataFrame({'date': forecast_dates, column: forecast})
    return monthly, forecast_df

# --- Main App ---
def main():
    st.set_page_config(page_title="Chocolate Sales Dashboard", layout="wide")
    
    # Initialize database
    conn = init_db()

    # --- Authentication ---
    if not st.session_state.logged_in:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            success, role = authenticate_user(username, password, conn)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
        st.sidebar.title("Register")
        new_username = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type="password")
        role = st.sidebar.selectbox("Role", ["Owner", "Sales Rep"])
        if st.sidebar.button("Register"):
            if add_user(new_username, new_password, role, conn):
                st.sidebar.success("User registered")
            else:
                st.sidebar.error("Username exists")
        return

    # --- Load Data ---
    if st.session_state.data is None:
        if os.path.exists(CSV_FILE_PATH):
            st.session_state.data = load_data()
        else:
            st.error(f"CSV file not found at {CSV_FILE_PATH}")
            return
    
    df = st.session_state.data.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Restrict Sales Reps to their own data
    if st.session_state.role == 'Sales Rep':
        df = df[df['sales_person'] == st.session_state.username]

    # --- Sidebar Filters ---
    st.sidebar.title("Filters")
    countries = st.sidebar.multiselect("Country", options=sorted(df['country'].unique()), default=df['country'].unique())
    products = st.sidebar.multiselect("Product", options=sorted(df['product'].unique()), default=df['product'].unique())
    sales_persons = st.sidebar.multiselect("Sales Person", options=sorted(df['sales_person'].unique()), default=df['sales_person'].unique())
    date_range = st.sidebar.date_input("Date Range", 
                                      [df['date'].min(), df['date'].max()],
                                      min_value=df['date'].min(),
                                      max_value=df['date'].max())
    amount_range = st.sidebar.slider("Amount Range", 
                                    float(df['amount'].min()), 
                                    float(df['amount'].max()), 
                                    (float(df['amount'].min()), float(df['amount'].max())))
    boxes_range = st.sidebar.slider("Boxes Shipped", 
                                   int(df['boxes_shipped'].min()), 
                                   int(df['boxes_shipped'].max()), 
                                   (int(df['boxes_shipped'].min()), int(df['boxes_shipped'].max())))
    sale_type = st.sidebar.multiselect("Sale Type", options=['Retail', 'Wholesale'], default=['Retail', 'Wholesale'])
    sort_by = st.sidebar.selectbox("Sort By", ['amount', 'boxes_shipped', 'date'])
    sort_order = st.sidebar.radio("Sort Order", ['Ascending', 'Descending'])

    # Apply Filters
    filtered_df = df[
        (df['country'].isin(countries)) &
        (df['product'].isin(products)) &
        (df['sales_person'].isin(sales_persons)) &
        (df['date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
        (df['amount'].between(amount_range[0], amount_range[1])) &
        (df['boxes_shipped'].between(boxes_range[0], boxes_range[1])) &
        (df['sale_type'].isin(sale_type))
    ]

    # Apply Sorting
    ascending = True if sort_order == 'Ascending' else False
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # --- Dashboard Layout ---
    st.title("Global Chocolate Sales Dashboard")

    # --- Top Performers ---
    st.header("Top Performers")
    col1, col2, col3 = st.columns(3)
    with col1:
        top_reps = filtered_df.groupby('sales_person')['amount'].sum().nlargest(5)
        st.subheader("Top 5 Sales Reps")
        for rep, amount in top_reps.items():
            if st.button(f"{rep}: ${amount:,.2f}", key=f"rep_{rep}"):
                st.session_state.data = filtered_df[filtered_df['sales_person'] == rep]
                st.experimental_rerun()
            st.metric(f"{rep}", f"${amount:,.2f}")
    with col2:
        top_products = filtered_df.groupby('product')['amount'].sum().nlargest(5)
        st.subheader("Top 5 Products")
        for prod, amount in top_products.items():
            if st.button(f"{prod}: ${amount:,.2f}", key=f"prod_{prod}"):
                st.session_state.data = filtered_df[filtered_df['product'] == prod]
                st.experimental_rerun()
            st.metric(f"{prod}", f"${amount:,.2f}")
    with col3:
        top_countries = filtered_df.groupby('country')['amount'].sum().nlargest(5)
        st.subheader("Top 5 Countries")
        for country, amount in top_countries.items():
            if st.button(f"{country}: ${amount:,.2f}", key=f"country_{country}"):
                st.session_state.data = filtered_df[filtered_df['country'] == country]
                st.experimental_rerun()
            st.metric(f"{country}", f"${amount:,.2f}")

    # --- Sales Trends ---
    st.header("Sales Trends")
    metric = st.selectbox("Metric", ['amount', 'boxes_shipped'])
    monthly = filtered_df.groupby(filtered_df['date'].dt.to_period('M'))[metric].sum().reset_index()
    monthly['date'] = monthly['date'].dt.to_timestamp()
    
    # Forecasting
    show_forecast = st.checkbox("Show Forecast")
    if show_forecast:
        historical, forecast_df = forecast_sales(filtered_df, metric)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=historical['date'], y=historical[metric], name='Historical'))
        fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df[metric], name='Forecast', line=dict(dash='dash')))
    else:
        fig = px.line(monthly, x='date', y=metric, title=f"{metric.replace('_', ' ').title()} Over Time")
    fig.update_layout(xaxis_title="Date", yaxis_title=metric.replace('_', ' ').title())
    st.plotly_chart(fig, use_container_width=True)

    # --- Bar Chart ---
    group_by = st.selectbox("Group By", ['country', 'product', 'sales_person'])
    bar_data = filtered_df.groupby(group_by)[metric].sum().reset_index()
    fig_bar = px.bar(bar_data, x=group_by, y=metric, title=f"{metric.replace('_', ' ').title()} by {group_by.replace('_', ' ').title()}")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Pie Chart ---
    pie_by = st.selectbox("Pie Chart By", ['country', 'product'])
    pie_data = filtered_df.groupby(pie_by)[metric].sum().reset_index()
    fig_pie = px.pie(pie_data, values=metric, names=pie_by, title=f"{metric.replace('_', ' ').title()} Distribution by {pie_by.replace('_', ' ').title()}")
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Sale Type Analysis ---
    st.header("Retail vs Wholesale")
    sale_type_counts = filtered_df['sale_type'].value_counts().reset_index()
    sale_type_counts.columns = ['sale_type', 'Count']
    fig_sale_type = px.pie(sale_type_counts, values='Count', names='sale_type', title="Retail vs Wholesale Distribution")
    st.plotly_chart(fig_sale_type, use_container_width=True)

    # Manual Sale Type Override (Owner only)
    if st.session_state.role == 'Owner':
        st.subheader("Override Sale Type")
        record_id = st.number_input("Record ID", min_value=1, step=1)
        new_sale_type = st.selectbox("New Sale Type", ['Retail', 'Wholesale'])
        if st.button("Update Sale Type"):
            conn = sqlite3.connect('sales_data.db')
            c = conn.cursor()
            c.execute('UPDATE sales SET sale_type = ? WHERE id = ?', (new_sale_type, record_id))
            conn.commit()
            conn.close()
            st.session_state.data = load_data_from_db()
            st.success("Sale type updated")

    # --- Global Sales Map ---
    st.header("Global Sales Map")
    country_sales = filtered_df.groupby('country')[metric].sum().reset_index()
    fig_map = px.choropleth(country_sales,
                            locations='country',
                            locationmode='country names',
                            color=metric,
                            hover_name='country',
                            color_continuous_scale=px.colors.sequential.Plasma,
                            title=f"{metric.replace('_', ' ').title()} by Country")
    st.plotly_chart(fig_map, use_container_width=True)

    # --- Product Performance ---
    st.header("Product Performance")
    # Categorize products
    def categorize_product(product):
        if 'Dark' in product:
            return 'Dark Chocolate'
        elif 'Milk' in product:
            return 'Milk Chocolate'
        elif 'Syrup' in product:
            return 'Syrups'
        else:
            return 'Other'
    
    filtered_df['Category'] = filtered_df['product'].apply(categorize_product)
    category_sales = filtered_df.groupby('Category')[metric].sum().reset_index()
    fig_category = px.bar(category_sales, x='Category', y=metric, title=f"{metric.replace('_', ' ').title()} by Product Category")
    st.plotly_chart(fig_category, use_container_width=True)

    # Seasonal Trends
    seasonal = filtered_df[filtered_df['product'] == 'Drinking Coco'].groupby(filtered_df['date'].dt.month)[metric].mean().reset_index()
    fig_seasonal = px.line(seasonal, x='date', y=metric, title="Drinking Coco Seasonal Trends")
    st.plotly_chart(fig_seasonal, use_container_width=True)

    # --- Data Table with CRUD ---
    st.header("Sales Data")
    if st.session_state.role == 'Owner':
        with st.expander("Add New Sale"):
            with st.form("add_sale_form"):
                new_sales_person = st.text_input("Sales Person")
                new_country = st.text_input("Country")
                new_product = st.text_input("Product")
                new_date = st.date_input("Date")
                new_amount = st.number_input("Amount", min_value=0.0)
                new_boxes = st.number_input("Boxes Shipped", min_value=0)
                new_sale_type = st.selectbox("Sale Type", ['Retail', 'Wholesale'])
                submit = st.form_submit_button("Add Sale")
                if submit:
                    conn = sqlite3.connect('sales_data.db')
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO sales (sales_person, country, product, date, amount, boxes_shipped, sale_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (new_sales_person, new_country, new_product, str(new_date), new_amount, new_boxes, new_sale_type))
                    conn.commit()
                    conn.close()
                    st.session_state.data = load_data_from_db()
                    st.success("Sale added")

    # Display Table
    st.dataframe(filtered_df, use_container_width=True)

    # Edit/Delete (Owner only)
    if st.session_state.role == 'Owner':
        st.subheader("Edit/Delete Sale")
        edit_id = st.number_input("Record ID to Edit/Delete", min_value=1, step=1)
        with st.form("edit_sale_form"):
            edit_sales_person = st.text_input("Sales Person", key="edit_sales_person")
            edit_country = st.text_input("Country", key="edit_country")
            edit_product = st.text_input("Product", key="edit_product")
            edit_date = st.date_input("Date", key="edit_date")
            edit_amount = st.number_input("Amount", min_value=0.0, key="edit_amount")
            edit_boxes = st.number_input("Boxes Shipped", min_value=0, key="edit_boxes")
            edit_sale_type = st.selectbox("Sale Type", ['Retail', 'Wholesale'], key="edit_sale_type")
            col_edit, col_delete = st.columns(2)
            with col_edit:
                edit_submit = st.form_submit_button("Update Sale")
            with col_delete:
                delete_submit = st.form_submit_button("Delete Sale")
            
            if edit_submit:
                conn = sqlite3.connect('sales_data.db')
                c = conn.cursor()
                c.execute('''
                    UPDATE sales SET sales_person = ?, country = ?, product = ?, date = ?,
                    amount = ?, boxes_shipped = ?, sale_type = ?
                    WHERE id = ?
                ''', (edit_sales_person, edit_country, edit_product, str(edit_date),
                      edit_amount, edit_boxes, edit_sale_type, edit_id))
                conn.commit()
                conn.close()
                st.session_state.data = load_data_from_db()
                st.success("Sale updated")
            
            if delete_submit:
                conn = sqlite3.connect('sales_data.db')
                c = conn.cursor()
                c.execute('DELETE FROM sales WHERE id = ?', (edit_id,))
                conn.commit()
                conn.close()
                st.session_state.data = load_data_from_db()
                st.success("Sale deleted")

    # --- Export Data ---
    st.subheader("Export Data")
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", csv, "filtered_sales.csv", "text/csv")

    # --- Anomaly Detection ---
    st.header("Anomaly Alerts")
    anomalies = filtered_df[filtered_df['amount'] > 15000]
    if not anomalies.empty:
        st.warning(f"Found {len(anomalies)} high-value sales (> $15,000)")
        st.dataframe(anomalies)
        if st.button("Dismiss Anomalies"):
            st.success("Anomalies dismissed")
    
    # Month-over-month drops
    monthly_changes = monthly[metric].pct_change() * 100
    drops = monthly_changes[monthly_changes < -50]
    if not drops.empty:
        st.warning(f"Significant month-over-month drops detected: {drops.index.tolist()}")
        if st.button("Dismiss Drops"):
            st.success("Drops dismissed")

if __name__ == "__main__":
    main()