# streamlit_app.py - Comprehensive RAG Pipeline UI

import streamlit as st
import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="RAG Pipeline Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
class Config:
    API_BASE_URL = "http://localhost:8000"
    TIMEOUT = 30
    
    @classmethod
    def get_headers(cls, token: str = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

# API Client
class APIClient:
    def __init__(self, base_url: str = Config.API_BASE_URL):
        self.base_url = base_url
        
    def health_check(self) -> Dict:
        """Check API health status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return {"status": "healthy", "data": response.json()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """Register a new user"""
        try:
            data = {
                "username": username,
                "email": email,
                "password": password
            }
            response = requests.post(
                f"{self.base_url}/auth/register",
                data=data,
                timeout=Config.TIMEOUT
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def login_user(self, username: str, password: str) -> Dict:
        """Login user and get access token"""
        try:
            data = {
                "username": username,
                "password": password
            }
            response = requests.post(
                f"{self.base_url}/auth/login",
                data=data,
                timeout=Config.TIMEOUT
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_files(self, files: List, token: str, async_processing: bool = False) -> Dict:
        """Upload files to the system"""
        try:
            files_data = [("files", (file.name, file, "application/pdf")) for file in files]
            data = {"async_processing": str(async_processing).lower()}
            
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{self.base_url}/upload",
                files=files_data,
                data=data,
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query_documents(self, query: str, token: str, k: int = 3, 
                       search_type: str = "hybrid", use_cache: bool = True) -> Dict:
        """Query documents using RAG"""
        try:
            data = {
                "query": query,
                "k": k,
                "search_type": search_type,
                "use_cache": str(use_cache).lower(),
                "expand_query": "true"
            }
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{self.base_url}/query",
                data=data,
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_documents(self, token: str, skip: int = 0, limit: int = 100) -> Dict:
        """List user's documents"""
        try:
            params = {"skip": skip, "limit": limit}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.base_url}/documents",
                params=params,
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_document(self, document_id: int, token: str) -> Dict:
        """Delete a document"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.delete(
                f"{self.base_url}/documents/{document_id}",
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self, token: str = None) -> Dict:
        """Get system statistics"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = requests.get(
                f"{self.base_url}/stats",
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_api_key(self, name: str, expires_days: int, token: str) -> Dict:
        """Create a new API key"""
        try:
            data = {
                "name": name,
                "expires_days": expires_days
            }
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{self.base_url}/auth/api-keys",
                data=data,
                headers=headers,
                timeout=Config.TIMEOUT
            )
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize API client
api_client = APIClient()

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "documents" not in st.session_state:
    st.session_state.documents = []

# Authentication functions
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user and store session data"""
    result = api_client.login_user(username, password)
    if result["success"]:
        data = result["data"]
        st.session_state.authenticated = True
        st.session_state.access_token = data["access_token"]
        
        # Handle different API response structures
        if "user" in data:
            # New API structure with nested user object
            st.session_state.user_info = data["user"]
        else:
            # Current API structure with flat user data
            st.session_state.user_info = {
                "id": data.get("user_id"),
                "username": data.get("username"),
                "role": data.get("role", "user")
            }
        return True
    else:
        st.error(f"Login failed: {result.get('error', 'Unknown error')}")
        return False

def logout_user():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.documents = []
    st.success("Logged out successfully!")

# UI Components
def render_health_status():
    """Render API health status"""
    health = api_client.health_check()
    if health["status"] == "healthy":
        st.success("🟢 API is healthy and running")
        with st.expander("Health Details"):
            st.json(health["data"])
    else:
        st.error(f"🔴 API is not responding: {health.get('error', 'Unknown error')}")

def render_authentication():
    """Render authentication interface"""
    st.markdown('<div class="main-header">🔍 RAG Pipeline Dashboard</div>', unsafe_allow_html=True)
    
    # Health check
    render_health_status()
    
    if not st.session_state.authenticated:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔐 Login")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("Login", use_container_width=True)
                
                if login_btn:
                    if username and password:
                        with st.spinner("Authenticating..."):
                            authenticate_user(username, password)
                    else:
                        st.error("Please enter both username and password")
        
        with col2:
            st.subheader("📝 Register")
            with st.form("register_form"):
                reg_username = st.text_input("Username", key="reg_username", placeholder="Choose a username")
                reg_email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
                reg_password = st.text_input("Password", key="reg_password", type="password", placeholder="Choose a password")
                register_btn = st.form_submit_button("Register", use_container_width=True)
                
                if register_btn:
                    if reg_username and reg_email and reg_password:
                        with st.spinner("Creating account..."):
                            result = api_client.register_user(reg_username, reg_email, reg_password)
                            if result["success"]:
                                st.success("Account created successfully! Please login.")
                                st.balloons()
                            else:
                                error_msg = result.get("error", "Registration failed")
                                if isinstance(error_msg, dict):
                                    error_msg = error_msg.get("detail", str(error_msg))
                                st.error(f"Registration failed: {error_msg}")
                    else:
                        st.error("Please fill in all fields")
    
    else:
        # User is authenticated
        st.sidebar.success(f"👋 Welcome, {st.session_state.user_info['username']}!")
        st.sidebar.write(f"**Role:** {st.session_state.user_info['role']}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

def render_document_manager():
    """Render document management interface"""
    st.header("📄 Document Management")
    
    # Upload section
    st.subheader("📤 Upload Documents")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            accept_multiple_files=True,
            type=['pdf'],
            help="Upload PDF documents to add to your knowledge base"
        )
    
    with col2:
        async_processing = st.checkbox("Async Processing", help="Process files in background")
        
        if st.button("🚀 Upload", use_container_width=True):
            if uploaded_files:
                with st.spinner("Uploading files..."):
                    result = api_client.upload_files(
                        uploaded_files, 
                        st.session_state.access_token,
                        async_processing
                    )
                    
                    if result["success"]:
                        data = result["data"]
                        st.success(f"✅ Uploaded {data.get('total_uploaded', 0)} files successfully!")
                        
                        # Show upload details
                        if data.get('uploaded'):
                            st.subheader("📋 Upload Results")
                            for doc in data['uploaded']:
                                with st.expander(f"📄 {doc['filename']}"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Pages", doc.get('pages', 0))
                                    with col2:
                                        st.metric("File Size", f"{doc.get('file_size', 0):,} bytes")
                                    with col3:
                                        st.metric("Status", doc.get('status', 'Unknown'))
                        
                        # Show errors if any
                        if data.get('errors'):
                            st.error("⚠️ Some files had errors:")
                            for error in data['errors']:
                                st.write(f"• {error}")
                        
                        # Refresh document list
                        refresh_documents()
                    else:
                        error_msg = result.get("error", "Upload failed")
                        st.error(f"❌ Upload failed: {error_msg}")
            else:
                st.warning("Please select files to upload")
    
    # Document list
    st.subheader("📚 Your Documents")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            refresh_documents()
    
    with col2:
        show_details = st.checkbox("Show Details", value=False)
    
    # Display documents
    if st.session_state.documents:
        for doc in st.session_state.documents:
            with st.expander(f"📄 {doc['filename']} ({doc.get('page_count', 0)} pages)"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Upload Date", doc['upload_date'][:10])
                
                with col2:
                    st.metric("File Size", f"{doc.get('file_size', 0):,} bytes")
                
                with col3:
                    st.metric("Chunks", doc.get('chunk_count', 0))
                
                with col4:
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}"):
                        delete_document(doc['id'], doc['filename'])
                
                if show_details and doc.get('metadata'):
                    st.json(doc['metadata'])
    else:
        st.info("📭 No documents uploaded yet. Upload some PDF files to get started!")

def refresh_documents():
    """Refresh the document list"""
    result = api_client.list_documents(st.session_state.access_token)
    if result["success"]:
        st.session_state.documents = result["data"].get("documents", [])
    else:
        st.error(f"Failed to load documents: {result.get('error', 'Unknown error')}")

def delete_document(doc_id: int, filename: str):
    """Delete a document with confirmation"""
    if st.checkbox(f"Confirm deletion of '{filename}'", key=f"confirm_{doc_id}"):
        result = api_client.delete_document(doc_id, st.session_state.access_token)
        if result["success"]:
            st.success(f"✅ Deleted '{filename}' successfully!")
            refresh_documents()
            st.rerun()
        else:
            st.error(f"❌ Failed to delete document: {result.get('error')}")

def render_query_interface():
    """Render the query interface"""
    st.header("🔍 Query Documents")
    
    # Query input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Ask a question about your documents:",
            placeholder="What are the main findings in the research papers?",
            height=100
        )
    
    with col2:
        st.write("**Query Options**")
        k = st.slider("Number of results", 1, 10, 3)
        search_type = st.selectbox("Search Type", ["hybrid", "semantic", "keyword"])
        use_cache = st.checkbox("Use Cache", value=True)
    
    # Query button
    if st.button("🚀 Ask Question", use_container_width=True):
        if query.strip():
            if not st.session_state.documents:
                st.warning("📭 No documents available. Please upload some documents first.")
                return
            
            with st.spinner("🤔 Thinking..."):
                start_time = time.time()
                result = api_client.query_documents(
                    query, 
                    st.session_state.access_token,
                    k=k,
                    search_type=search_type,
                    use_cache=use_cache
                )
                end_time = time.time()
                
                if result["success"]:
                    data = result["data"]
                    
                    # Display answer
                    st.subheader("💡 Answer")
                    st.markdown(data["answer"])
                    
                    # Display metadata
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Processing Time", f"{data.get('processing_time', 0):.3f}s")
                    
                    with col2:
                        st.metric("Documents Searched", data.get('documents_searched', 0))
                    
                    with col3:
                        cache_status = "Yes" if data.get('cached', False) else "No"
                        st.metric("Cached Response", cache_status)
                    
                    with col4:
                        st.metric("Search Type", data.get('search_type', 'Unknown'))
                    
                    # Show expanded query if available
                    if data.get('processed_query') and data['processed_query'] != query:
                        with st.expander("🔍 Query Expansion"):
                            st.write("**Original Query:**", query)
                            st.write("**Expanded Query:**", data['processed_query'])
                    
                else:
                    error_msg = result.get("error", "Query failed")
                    st.error(f"❌ Query failed: {error_msg}")
        else:
            st.warning("Please enter a question")

def render_api_keys():
    """Render API key management interface"""
    st.header("🔑 API Key Management")
    
    st.info("API keys provide an alternative authentication method for programmatic access.")
    
    # Create new API key
    st.subheader("➕ Create New API Key")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        key_name = st.text_input("API Key Name", placeholder="My Application Key")
    
    with col2:
        expires_days = st.number_input("Expires in (days)", min_value=1, max_value=365, value=30)
    
    with col3:
        st.write("")  # Spacing
        if st.button("🔑 Create Key", use_container_width=True):
            if key_name:
                result = api_client.create_api_key(key_name, expires_days, st.session_state.access_token)
                if result["success"]:
                    data = result["data"]
                    st.success("✅ API Key created successfully!")
                    
                    # Show the API key (only shown once)
                    st.warning("⚠️ **Save this API key now! It will not be shown again.**")
                    st.code(data["api_key"], language="text")
                    
                    st.info(f"**Key ID:** {data['key_id']}")
                    st.info(f"**Expires:** {data['expires_at']}")
                else:
                    st.error(f"❌ Failed to create API key: {result.get('error')}")
            else:
                st.warning("Please enter a name for the API key")

def render_monitoring():
    """Render system monitoring dashboard"""
    st.header("📊 System Monitoring")
    
    # Get system statistics
    result = api_client.get_stats(st.session_state.access_token)
    
    if result["success"]:
        stats = result["data"]
        
        # Overview metrics
        st.subheader("📈 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            doc_count = stats.get("documents", {}).get("accessible", 0)
            st.metric("📄 Accessible Documents", doc_count)
        
        with col2:
            total_pages = stats.get("documents", {}).get("total_pages", 0)
            st.metric("📚 Total Pages", f"{total_pages:,}")
        
        with col3:
            total_queries = stats.get("queries", {}).get("total", 0)
            st.metric("🔍 Total Queries", f"{total_queries:,}")
        
        with col4:
            avg_time = stats.get("queries", {}).get("average_processing_time", 0)
            st.metric("⚡ Avg Query Time", f"{avg_time:.3f}s")
        
        # Cache statistics
        if stats.get("cache"):
            st.subheader("💾 Cache Performance")
            
            cache_stats = stats["cache"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                query_cache = cache_stats.get("query_cache", {})
                hit_rate = query_cache.get("hit_rate", 0)
                st.metric("Query Cache Hit Rate", f"{hit_rate:.1%}")
            
            with col2:
                embedding_cache = cache_stats.get("embedding_cache", {})
                embed_hits = embedding_cache.get("hits", 0)
                st.metric("Embedding Cache Hits", f"{embed_hits:,}")
            
            with col3:
                doc_cache = cache_stats.get("document_cache", {})
                doc_hits = doc_cache.get("hits", 0)
                st.metric("Document Cache Hits", f"{doc_hits:,}")
        
        # Performance metrics
        if stats.get("performance"):
            st.subheader("⚡ Performance Metrics")
            
            perf_data = []
            for metric_name, metric_stats in stats["performance"].items():
                if isinstance(metric_stats, dict):
                    perf_data.append({
                        "Metric": metric_name,
                        "Count": metric_stats.get("count", 0),
                        "Average": f"{metric_stats.get('average', 0):.3f}s",
                        "Min": f"{metric_stats.get('min', 0):.3f}s",
                        "Max": f"{metric_stats.get('max', 0):.3f}s"
                    })
            
            if perf_data:
                df = pd.DataFrame(perf_data)
                st.dataframe(df, use_container_width=True)
        
        # System information
        if stats.get("system"):
            st.subheader("🖥️ System Information")
            
            system_stats = stats["system"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.json(system_stats)
            
            with col2:
                # Create a simple chart if we have numeric data
                if isinstance(system_stats, dict):
                    numeric_data = []
                    for key, value in system_stats.items():
                        if isinstance(value, (int, float)):
                            numeric_data.append({"Metric": key, "Value": value})
                    
                    if numeric_data:
                        df = pd.DataFrame(numeric_data)
                        fig = px.bar(df, x="Metric", y="Value", title="System Metrics")
                        st.plotly_chart(fig, use_container_width=True)
        
        # Error tracking
        if stats.get("errors"):
            st.subheader("🚨 Error Tracking")
            
            error_stats = stats["errors"]
            if error_stats:
                st.warning(f"Recent errors detected: {error_stats}")
            else:
                st.success("✅ No recent errors")
        
        # Task statistics
        if stats.get("tasks"):
            st.subheader("📋 Background Tasks")
            
            task_stats = stats["tasks"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tasks", task_stats.get("total", 0))
            
            with col2:
                st.metric("Running", task_stats.get("running", 0))
            
            with col3:
                st.metric("Completed", task_stats.get("completed", 0))
            
            with col4:
                st.metric("Failed", task_stats.get("failed", 0))
            
            # Task status pie chart
            task_data = []
            for status in ["pending", "running", "completed", "failed"]:
                count = task_stats.get(status, 0)
                if count > 0:
                    task_data.append({"Status": status.title(), "Count": count})
            
            if task_data:
                fig = px.pie(
                    pd.DataFrame(task_data), 
                    values="Count", 
                    names="Status",
                    title="Task Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.error(f"❌ Failed to load system statistics: {result.get('error')}")

# Main application
def main():
    """Main application entry point"""
    
    # Always show authentication first
    render_authentication()
    
    # Only show main app if authenticated
    if st.session_state.authenticated:
        
        # Sidebar navigation
        st.sidebar.title("🧭 Navigation")
        
        pages = {
            "📄 Document Manager": render_document_manager,
            "🔍 Query Interface": render_query_interface,
            "🔑 API Keys": render_api_keys,
            "📊 Monitoring": render_monitoring
        }
        
        selected_page = st.sidebar.selectbox("Choose a page:", list(pages.keys()))
        
        # Refresh documents if not loaded
        if not st.session_state.documents and selected_page in ["📄 Document Manager", "🔍 Query Interface"]:
            with st.spinner("Loading documents..."):
                refresh_documents()
        
        # Render selected page
        pages[selected_page]()
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 RAG Pipeline Dashboard**")
        st.sidebar.markdown("Built with Streamlit")

if __name__ == "__main__":
    main()
