import streamlit as st
import requests
import os
import time

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") # Backend URL

st.set_page_config(page_title="Data Connectors", page_icon="🔌", layout="wide")

st.title("🔌 Data Connectors")
st.markdown("Manage your cloud storage connections here.")

# --- Helper Functions ---
def get_connectors():
    try:
        response = requests.get(f"{API_BASE_URL}/api/connectors/")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch connectors: {e}")
        return []

def delete_connector(connector_id):
    try:
        response = requests.delete(f"{API_BASE_URL}/api/connectors/{connector_id}")
        if response.status_code == 200:
            st.success("Connector deleted!")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Failed to delete: {response.text}")
    except Exception as e:
        st.error(f"Error: {e}")

def trigger_sync(connector_id):
    try:
        response = requests.post(f"{API_BASE_URL}/api/connectors/{connector_id}/sync")
        if response.status_code == 200:
            st.toast("Sync started!", icon="🔄")
        else:
            st.error("Failed to start sync")
    except Exception as e:
        st.error(f"Error: {e}")

# --- UI ---

# 1. List Connectors
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Active Connectors")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

connectors = get_connectors()

if not connectors:
    st.info("No connectors configured.")
else:
    for c in connectors:
        with st.expander(f"{c['provider'].replace('_', ' ').title()}: {c['name']}", expanded=True):
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**ID:** `{c['id']}`")
            cols[1].write(f"**Status:** {'✅ Enabled' if c['enabled'] else '❌ Disabled'}")
            
            last_sync = c.get('last_sync')
            cols[2].write(f"**Last Sync:** {last_sync if last_sync else 'Never'}")
            
            with cols[3]:
                if st.button("Sync Now", key=f"sync_{c['id']}"):
                    trigger_sync(c['id'])
                if st.button("Delete", key=f"del_{c['id']}", type="primary"):
                    delete_connector(c['id'])
                
            st.caption(f"Folders: {c['folders_to_sync']}")
            st.caption(f"Strategy: {c['sync_strategy']} ({c['sync_interval']}m)")

st.divider()

# 2. Add Connector
st.subheader("Add New Connector")

with st.form("add_connector_form"):
    provider = st.selectbox("Provider", ["google_drive", "onedrive"])
    name = st.text_input("Name (e.g. My Shared Drive)")
    
    # Configuration
    folders = st.text_input("Folder ID (e.g. root or specific folder ID)")
    
    submitted = st.form_submit_button("Create Connector")
    
    if submitted:
        if not name or not folders:
            st.error("Please provide name and folder ID.")
        else:
            payload = {
                "name": name,
                "provider": provider,
                "folders_to_sync": [folders.strip()],
                "sync_strategy": "polling",
                "sync_interval": 15
            }
            
            try:
                # 1. Create in DB
                res = requests.post(f"{API_BASE_URL}/api/connectors/", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    new_id = data["id"]
                    st.success(f"Connector created! User ID: {new_id}")
                    
                    # 2. Trigger OAuth
                    # API endpoint to get Auth URL
                    # We pass the redirect URI which should be the backend callback
                    redirect = f"{API_BASE_URL}/api/connectors/oauth/callback/{provider}?connector_id={new_id}"
                    # Note: We append connector_id as query param to callback so backend knows which one to update! 
                    # But normally state param avoids this. For now let's append.
                     
                    auth_res = requests.get(
                        f"{API_BASE_URL}/api/connectors/oauth/authorize/{provider}",
                        params={
                            "redirect_uri": f"{API_BASE_URL}/api/connectors/oauth/callback/{provider}",
                            "connector_id": new_id
                        }
                    )
                    
                    # For now, let's just show the link if we can get it
                    if auth_res.status_code == 200:
                        url = auth_res.json().get("authorization_url")
                        # Add state param manually if backend didn't?
                        # Actually base implementation of `authorize_connector` did not handle state!
                        # I need to fix backend to use `state` for connector_id.
                        
                        st.markdown(f"### 👉 [Click here to Authorize with {provider}]({url})")
                        st.info("After authorization, return here and refresh.")
                    else:
                        st.error("Failed to get authorization URL")
                        
                else:
                    st.error(f"Failed to create: {res.text}")
                    
            except Exception as e:
                st.error(f"Error: {e}")
