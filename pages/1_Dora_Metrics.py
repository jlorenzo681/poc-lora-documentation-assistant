
import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="DORA Metrics", page_icon="📊", layout="wide")

st.title("📊 DORA Metrics Dashboard")
st.markdown("Measuring software delivery performance.")

# --- Database Connection ---
@st.cache_resource
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "shared-db"), # Default internal docker name, might need "localhost" if running outside docker with port fwd
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
    except Exception as e:
        return None

def fetch_data(query, params=None):
    conn = get_db_connection()
    if not conn:
        st.error("Stats DB Connection Failed")
        return pd.DataFrame()
    
    try:
        # Reconnect if closed
        if conn.closed:
            conn = get_db_connection() 
            
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return pd.DataFrame(data, columns=columns)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Query Error: {e}")
        return pd.DataFrame()
    # Note: We keep connection open for cache_resource, or we should close it? 
    # With cache_resource, we share it. But psycopg2 connection is not thread safe for write.
    # For read it might be okay if cursors are distinct. 
    # Safest is to create new connection per request or use a pool.
    # For this low traffic internal app, let's just make a fresh connection function without cache for safety,
    # or handle it carefully. Let's remove cache_resource for the connection itself and cache data.

# Redefine without cache for safety
def get_safe_connection():
     try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "shared-db"),
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
     except:
         return None

def run_query(query, params=None):
    conn = get_safe_connection()
    if not conn:
        # Fallback for local dev if 'shared-db' fails, try localhost
        try:
             conn = psycopg2.connect(
                host="localhost",
                database=os.getenv("POSTGRES_DB", "postgres"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                port="5432" # Assumes port forward
            )
        except:
             st.error("Could not connect to database (tried shared-db and localhost)")
             return pd.DataFrame()

    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- Time Range Selector ---
days = st.slider("Select Time Range (Days)", min_value=7, max_value=90, value=30)
start_date = datetime.now() - timedelta(days=days)

# --- Metrics Calculation ---

# 1. Deployment Frequency
st.header("1. Deployment Frequency")
df_deploy = run_query("""
    SELECT DATE(timestamp) as date, COUNT(*) as count
    FROM dora_metrics
    WHERE metric_type = 'deployment'
    AND timestamp >= %s
    GROUP BY DATE(timestamp)
    ORDER BY date
""", (start_date,))

if not df_deploy.empty:
    fig_deploy = px.bar(df_deploy, x='date', y='count', title="Daily Deployments")
    st.plotly_chart(fig_deploy, use_container_width=True)
    
    total_deploys = df_deploy['count'].sum()
    freq = total_deploys / days
    st.metric("Deployments / Day", f"{freq:.2f}")
else:
    st.info("No deployment data available.")

# 2. Lead Time for Changes
st.header("2. Lead Time for Changes")
df_lead = run_query("""
    SELECT timestamp, value as minutes
    FROM dora_metrics
    WHERE metric_type = 'lead_time'
    AND timestamp >= %s
""", (start_date,))

if not df_lead.empty:
    avg_lead = df_lead['minutes'].mean()
    st.metric("Average Lead Time", f"{avg_lead:.1f} minutes")
    
    fig_lead = px.scatter(df_lead, x='timestamp', y='minutes', title="Lead Time per Change")
    st.plotly_chart(fig_lead, use_container_width=True)
else:
    st.info("No lead time data available.")

# 3. Change Failure Rate
st.header("3. Change Failure Rate")
col1, col2 = st.columns(2)

with col1:
    total_deployments = run_query("""
        SELECT COUNT(*) as count FROM dora_metrics 
        WHERE metric_type = 'deployment' AND timestamp >= %s
    """, (start_date,)).iloc[0]['count']
    
    total_failures = run_query("""
        SELECT COUNT(*) as count FROM dora_metrics 
        WHERE metric_type = 'failure' AND timestamp >= %s
    """, (start_date,)).iloc[0]['count']

    cfr = (total_failures / total_deployments * 100) if total_deployments > 0 else 0.0
    st.metric("Change Failure Rate (CFR)", f"{cfr:.1f}%")

# 4. Time to Restore Service
st.header("4. Time to Restore Service (MTTR)")
df_mttr = run_query("""
    SELECT AVG(value) as avg_mttr
    FROM dora_metrics
    WHERE metric_type = 'restore'
    AND timestamp >= %s
""", (start_date,))

if not df_mttr.empty and df_mttr.iloc[0]['avg_mttr'] is not None:
    mttr = df_mttr.iloc[0]['avg_mttr']
    st.metric("Mean Time to Restore", f"{mttr:.1f} minutes")
else:
    st.info("No MTTR data available.")


# --- Manual Data Entry (For Testing) ---
with st.expander("🛠 Developer Tools: Record Events manually"):
    st.write("Use this to simulate events for testing the dashboard.")
    
    tab1, tab2, tab3 = st.tabs(["Record Deployment", "Record Failure", "Incident"])
    
    with tab1:
        if st.button("Simulate Deployment"):
            # We can't easily import backend classes here if paths differ in docker vs local
            # So we use direct SQL or calling the utility if path works.
            # Let's try direct SQL for simplicity in this frontend page
            try:
                conn = get_safe_connection()
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO dora_metrics (metric_type, value, timestamp) VALUES ('deployment', 1, NOW())")
                    conn.commit()
                    conn.close()
                    st.success("recorded!")
                    st.rerun()
            except Exception as e:
                st.error(str(e))
                
    with tab2:
        if st.button("Simulate Failure"):
            try:
                conn = get_safe_connection()
                if conn:
                    with conn.cursor() as cur:
                         cur.execute("INSERT INTO dora_metrics (metric_type, value, timestamp) VALUES ('failure', 1, NOW())")
                    conn.commit()
                    conn.close()
                    st.success("recorded!")
                    st.rerun()
            except Exception as e:
                st.error(str(e))
