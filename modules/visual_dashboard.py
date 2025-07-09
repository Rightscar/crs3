"""
Visual Dashboard Module
Provides real-time monitoring dashboard for logs, memory, sessions, and system health.
"""

import streamlit as st
import os
import json
import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from .performance_optimizer import performance_optimizer
    from .async_session_manager import AsyncSessionManager
    from .enhanced_logging import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from modules.performance_optimizer import performance_optimizer
        from modules.async_session_manager import AsyncSessionManager
        from modules.enhanced_logging import get_logger
    except ImportError:
        # Create mock objects if modules not available
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass
        
        def get_logger(name):
            return MockLogger()
        
        performance_optimizer = None
        AsyncSessionManager = None

class VisualDashboard:
    """
    Visual dashboard for monitoring system health, logs, and performance.
    """
    
    def __init__(self):
        """Initialize the visual dashboard"""
        self.logger = get_logger(__name__)
        self.session_manager = AsyncSessionManager() if AsyncSessionManager else None
        self.log_file_path = "logs/app.log"
        self.performance_log_path = "logs/performance.log"
        
        # Ensure log directories exist
        os.makedirs("logs", exist_ok=True)
        
    def render_dashboard(self):
        """Render the complete monitoring dashboard"""
        st.title("📊 System Monitoring Dashboard")
        
        # Auto-refresh controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        
        with col2:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear Logs"):
                self._clear_logs()
                st.success("Logs cleared!")
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🖥️ System Health", 
            "📝 Application Logs", 
            "👥 Active Sessions", 
            "⚡ Performance Metrics",
            "🔍 Detailed Analytics"
        ])
        
        with tab1:
            self._render_system_health()
        
        with tab2:
            self._render_application_logs()
        
        with tab3:
            self._render_active_sessions()
        
        with tab4:
            self._render_performance_metrics()
        
        with tab5:
            self._render_detailed_analytics()
    
    def _render_system_health(self):
        """Render system health monitoring"""
        st.subheader("🖥️ System Health Overview")
        
        # Get system metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # System metrics cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "CPU Usage",
                    f"{cpu_percent:.1f}%",
                    delta=f"{cpu_percent - 50:.1f}%" if cpu_percent > 50 else None
                )
            
            with col2:
                memory_percent = memory.percent
                st.metric(
                    "Memory Usage",
                    f"{memory_percent:.1f}%",
                    delta=f"{memory_percent - 70:.1f}%" if memory_percent > 70 else None
                )
            
            with col3:
                disk_percent = (disk.used / disk.total) * 100
                st.metric(
                    "Disk Usage",
                    f"{disk_percent:.1f}%",
                    delta=f"{disk_percent - 80:.1f}%" if disk_percent > 80 else None
                )
            
            with col4:
                # Application-specific memory
                if performance_optimizer:
                    app_memory = performance_optimizer.monitor_memory_usage()
                    st.metric(
                        "App Memory",
                        f"{app_memory.get('rss_mb', 0):.1f}MB",
                        delta=f"{app_memory.get('rss_mb', 0) - 100:.1f}MB" if app_memory.get('rss_mb', 0) > 100 else None
                    )
                else:
                    st.metric("App Memory", "N/A")
            
            # Health status indicators
            st.subheader("🚦 Health Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if cpu_percent < 70:
                    st.success("✅ CPU: Healthy")
                elif cpu_percent < 90:
                    st.warning("⚠️ CPU: High Usage")
                else:
                    st.error("🔴 CPU: Critical")
            
            with col2:
                if memory_percent < 70:
                    st.success("✅ Memory: Healthy")
                elif memory_percent < 90:
                    st.warning("⚠️ Memory: High Usage")
                else:
                    st.error("🔴 Memory: Critical")
            
            with col3:
                if disk_percent < 80:
                    st.success("✅ Disk: Healthy")
                elif disk_percent < 95:
                    st.warning("⚠️ Disk: High Usage")
                else:
                    st.error("🔴 Disk: Critical")
            
            # Real-time system chart
            self._render_realtime_system_chart()
            
        except Exception as e:
            st.error(f"Error retrieving system metrics: {str(e)}")
    
    def _render_application_logs(self):
        """Render application logs viewer"""
        st.subheader("📝 Application Logs")
        
        # Log level filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_level = st.selectbox(
                "Log Level",
                options=["ALL", "ERROR", "WARNING", "INFO", "DEBUG"],
                index=0
            )
        
        with col2:
            max_lines = st.number_input(
                "Max Lines",
                min_value=10,
                max_value=1000,
                value=100,
                step=10
            )
        
        with col3:
            search_term = st.text_input("Search in logs", placeholder="Enter search term...")
        
        # Read and display logs
        try:
            logs = self._read_log_file(self.log_file_path, max_lines, log_level, search_term)
            
            if logs:
                # Log statistics
                log_stats = self._analyze_logs(logs)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Entries", len(logs))
                col2.metric("Errors", log_stats.get('ERROR', 0))
                col3.metric("Warnings", log_stats.get('WARNING', 0))
                col4.metric("Info", log_stats.get('INFO', 0))
                
                # Log entries display
                st.subheader("Recent Log Entries")
                
                for log_entry in logs[-50:]:  # Show last 50 entries
                    timestamp = log_entry.get('timestamp', 'Unknown')
                    level = log_entry.get('level', 'INFO')
                    message = log_entry.get('message', '')
                    
                    # Color code by level
                    if level == 'ERROR':
                        st.error(f"🔴 **{timestamp}** - {message}")
                    elif level == 'WARNING':
                        st.warning(f"⚠️ **{timestamp}** - {message}")
                    elif level == 'INFO':
                        st.info(f"ℹ️ **{timestamp}** - {message}")
                    else:
                        st.text(f"📝 **{timestamp}** - {message}")
                
                # Download logs
                if st.button("📥 Download Logs"):
                    log_content = "\n".join([f"{entry.get('timestamp', '')} - {entry.get('level', '')} - {entry.get('message', '')}" for entry in logs])
                    st.download_button(
                        label="Download log file",
                        data=log_content,
                        file_name=f"app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            else:
                st.info("No log entries found matching the criteria.")
                
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")
    
    def _render_active_sessions(self):
        """Render active sessions monitoring"""
        st.subheader("👥 Active Sessions")
        
        if not self.session_manager:
            st.warning("Session manager not available")
            return
        
        try:
            # Get session information
            system_status = self.session_manager.get_system_status()
            active_sessions = system_status.get('active_sessions', 0)
            total_sessions = system_status.get('total_sessions_created', 0)
            
            # Session metrics
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Active Sessions", active_sessions)
            col2.metric("Total Created", total_sessions)
            col3.metric("Max Concurrent", system_status.get('max_concurrent_users', 10))
            col4.metric("System Load", f"{(active_sessions / system_status.get('max_concurrent_users', 10) * 100):.1f}%")
            
            # Session details
            if hasattr(self.session_manager, 'sessions') and self.session_manager.sessions:
                st.subheader("Session Details")
                
                session_data = []
                for session_id, session in self.session_manager.sessions.items():
                    session_data.append({
                        "Session ID": session_id[:8] + "...",
                        "User ID": session.user_id,
                        "Created": datetime.fromtimestamp(session.created_at).strftime("%H:%M:%S"),
                        "Last Activity": datetime.fromtimestamp(session.last_activity).strftime("%H:%M:%S"),
                        "Status": "Active" if not session.is_expired() else "Expired",
                        "Memory (MB)": f"{session.memory_usage:.1f}" if hasattr(session, 'memory_usage') else "N/A"
                    })
                
                if session_data:
                    df = pd.DataFrame(session_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No active sessions")
            else:
                st.info("No session data available")
                
        except Exception as e:
            st.error(f"Error retrieving session information: {str(e)}")
    
    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.subheader("⚡ Performance Metrics")
        
        if not performance_optimizer:
            st.warning("Performance optimizer not available")
            return
        
        try:
            # Get performance statistics
            perf_stats = performance_optimizer.get_performance_stats()
            
            # Performance overview
            col1, col2, col3, col4 = st.columns(4)
            
            memory_stats = perf_stats.get('memory', {})
            col1.metric("Memory Usage", f"{memory_stats.get('rss_mb', 0):.1f}MB")
            col2.metric("Memory %", f"{memory_stats.get('percent', 0):.1f}%")
            
            system_stats = perf_stats.get('system', {})
            col3.metric("CPU %", f"{system_stats.get('cpu_percent', 0):.1f}%")
            col4.metric("Load Avg", f"{system_stats.get('load_avg', [0])[0]:.2f}")
            
            # Cache performance
            if hasattr(performance_optimizer, 'cache'):
                st.subheader("🗄️ Cache Performance")
                
                cache_stats = performance_optimizer.cache.stats()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Cache Size", cache_stats.get('size', 0))
                col2.metric("Hit Rate", f"{cache_stats.get('hit_rate', 0) * 100:.1f}%")
                col3.metric("Hits", cache_stats.get('hits', 0))
                col4.metric("Misses", cache_stats.get('misses', 0))
            
            # Performance trends chart
            self._render_performance_trends()
            
        except Exception as e:
            st.error(f"Error retrieving performance metrics: {str(e)}")
    
    def _render_detailed_analytics(self):
        """Render detailed analytics and insights"""
        st.subheader("🔍 Detailed Analytics")
        
        # Time range selector
        col1, col2 = st.columns(2)
        
        with col1:
            time_range = st.selectbox(
                "Time Range",
                options=["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"],
                index=1
            )
        
        with col2:
            metric_type = st.selectbox(
                "Metric Type",
                options=["System Performance", "User Activity", "Error Analysis", "Processing Stats"],
                index=0
            )
        
        # Generate analytics based on selection
        if metric_type == "System Performance":
            self._render_system_performance_analytics(time_range)
        elif metric_type == "User Activity":
            self._render_user_activity_analytics(time_range)
        elif metric_type == "Error Analysis":
            self._render_error_analysis(time_range)
        elif metric_type == "Processing Stats":
            self._render_processing_analytics(time_range)
    
    def _render_realtime_system_chart(self):
        """Render real-time system monitoring chart"""
        try:
            # Generate sample data for demonstration
            timestamps = [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)]
            cpu_data = [psutil.cpu_percent() + (i % 10 - 5) for i in range(30)]
            memory_data = [psutil.virtual_memory().percent + (i % 8 - 4) for i in range(30)]
            
            # Create subplot
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('CPU Usage (%)', 'Memory Usage (%)'),
                vertical_spacing=0.1
            )
            
            # Add CPU trace
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=cpu_data,
                    mode='lines+markers',
                    name='CPU %',
                    line=dict(color='#ff6b6b', width=2)
                ),
                row=1, col=1
            )
            
            # Add Memory trace
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=memory_data,
                    mode='lines+markers',
                    name='Memory %',
                    line=dict(color='#4ecdc4', width=2)
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                title_text="Real-time System Monitoring (Last 30 minutes)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering system chart: {str(e)}")
    
    def _render_performance_trends(self):
        """Render performance trends chart"""
        try:
            # Sample performance data
            timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
            response_times = [0.5 + (i % 5) * 0.1 for i in range(24)]
            throughput = [100 + (i % 10) * 5 for i in range(24)]
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Response Time (seconds)', 'Throughput (requests/min)'),
                vertical_spacing=0.1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=response_times,
                    mode='lines+markers',
                    name='Response Time',
                    line=dict(color='#ff9f43', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=throughput,
                    mode='lines+markers',
                    name='Throughput',
                    line=dict(color='#10ac84', width=2)
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                title_text="Performance Trends (Last 24 hours)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering performance trends: {str(e)}")
    
    def _read_log_file(self, file_path: str, max_lines: int, level_filter: str, search_term: str) -> List[Dict]:
        """Read and parse log file"""
        logs = []
        
        if not os.path.exists(file_path):
            return logs
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines[-max_lines:]:
                if line.strip():
                    # Simple log parsing (adjust based on your log format)
                    parts = line.strip().split(' - ', 2)
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        level = parts[1]
                        message = parts[2]
                        
                        # Apply filters
                        if level_filter != "ALL" and level != level_filter:
                            continue
                        
                        if search_term and search_term.lower() not in message.lower():
                            continue
                        
                        logs.append({
                            'timestamp': timestamp,
                            'level': level,
                            'message': message
                        })
            
        except Exception as e:
            st.error(f"Error reading log file: {str(e)}")
        
        return logs
    
    def _analyze_logs(self, logs: List[Dict]) -> Dict[str, int]:
        """Analyze logs and return statistics"""
        stats = {}
        
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            stats[level] = stats.get(level, 0) + 1
        
        return stats
    
    def _render_system_performance_analytics(self, time_range: str):
        """Render system performance analytics"""
        st.write("📊 System Performance Analytics")
        
        # Sample data for demonstration
        data = {
            'Metric': ['CPU Usage', 'Memory Usage', 'Disk I/O', 'Network I/O'],
            'Average': [45.2, 67.8, 23.1, 12.5],
            'Peak': [89.3, 92.1, 78.4, 45.2],
            'Status': ['Good', 'Warning', 'Good', 'Good']
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Performance chart
        fig = px.bar(df, x='Metric', y=['Average', 'Peak'], 
                     title=f"System Performance - {time_range}")
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_user_activity_analytics(self, time_range: str):
        """Render user activity analytics"""
        st.write("👥 User Activity Analytics")
        
        # Sample user activity data
        activity_data = {
            'Hour': list(range(24)),
            'Active Users': [2, 1, 0, 0, 1, 3, 5, 8, 12, 15, 18, 20, 22, 25, 23, 20, 18, 15, 12, 8, 6, 4, 3, 2],
            'Sessions Created': [1, 0, 0, 0, 1, 2, 3, 5, 8, 10, 12, 15, 18, 20, 18, 15, 12, 10, 8, 5, 3, 2, 1, 1]
        }
        
        df = pd.DataFrame(activity_data)
        
        fig = px.line(df, x='Hour', y=['Active Users', 'Sessions Created'],
                      title=f"User Activity - {time_range}")
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_error_analysis(self, time_range: str):
        """Render error analysis"""
        st.write("🔍 Error Analysis")
        
        # Sample error data
        error_data = {
            'Error Type': ['Import Error', 'API Timeout', 'Memory Error', 'File Not Found', 'Permission Error'],
            'Count': [5, 12, 2, 8, 3],
            'Severity': ['Medium', 'High', 'Critical', 'Low', 'Medium']
        }
        
        df = pd.DataFrame(error_data)
        
        fig = px.pie(df, values='Count', names='Error Type',
                     title=f"Error Distribution - {time_range}")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
    
    def _render_processing_analytics(self, time_range: str):
        """Render processing analytics"""
        st.write("⚙️ Processing Analytics")
        
        # Sample processing data
        processing_data = {
            'Operation': ['Text Extraction', 'Chunking', 'GPT Generation', 'Export'],
            'Total Requests': [150, 145, 140, 138],
            'Success Rate': [98.7, 97.2, 95.8, 99.3],
            'Avg Time (s)': [2.3, 1.8, 8.5, 0.9]
        }
        
        df = pd.DataFrame(processing_data)
        st.dataframe(df, use_container_width=True)
        
        # Processing performance chart
        fig = px.bar(df, x='Operation', y='Avg Time (s)',
                     title=f"Processing Performance - {time_range}")
        st.plotly_chart(fig, use_container_width=True)
    
    def _clear_logs(self):
        """Clear all log files"""
        try:
            log_files = [self.log_file_path, self.performance_log_path]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'w') as f:
                        f.write("")
            
            self.logger.info("Log files cleared by user")
            
        except Exception as e:
            st.error(f"Error clearing logs: {str(e)}")

# Global instance
visual_dashboard = VisualDashboard()

def render_visual_dashboard():
    """
    Convenience function to render the visual dashboard
    """
    visual_dashboard.render_dashboard()

