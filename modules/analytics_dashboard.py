"""
Analytics Dashboard Module
=========================

Comprehensive analytics and performance monitoring for the Universal Document Reader & AI Processor.
Tracks usage, performance metrics, and provides insights for optimization.

Features:
- Real-time performance monitoring
- Usage analytics and statistics
- Processing quality metrics
- System health monitoring
- Interactive visualizations
"""

import time
import logging

# Optional psutil import for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from typing import Dict, List, Any, Optional

# Optional streamlit import for UI components
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

# Optional dependencies for enhanced analytics
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available - analytics visualizations disabled")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("Pandas not available - data analysis features limited")

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric data"""
    timestamp: float
    metric_type: str
    value: float
    metadata: Dict[str, Any] = None

@dataclass
class ProcessingEvent:
    """Processing event for analytics"""
    timestamp: float
    event_type: str
    page_number: int
    processing_mode: str
    duration: float
    success: bool
    result_count: int
    confidence_avg: float
    metadata: Dict[str, Any] = None

@dataclass
class SessionAnalytics:
    """Complete session analytics"""
    session_id: str
    start_time: float
    end_time: Optional[float]
    documents_processed: int
    total_pages_processed: int
    total_processing_operations: int
    average_processing_time: float
    success_rate: float
    performance_metrics: List[PerformanceMetric]
    processing_events: List[ProcessingEvent]

class AnalyticsDashboard:
    """Analytics and performance monitoring dashboard"""
    
    def __init__(self):
        self.session_start = time.time()
        self.metrics_history = []
        self.processing_events = []
        self.performance_cache = {}
        
        # Initialize session analytics
        if 'analytics_session_id' not in st.session_state:
            st.session_state.analytics_session_id = f"session_{int(time.time())}"
        
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {
                'performance_metrics': [],
                'processing_events': [],
                'system_stats': [],
                'user_interactions': []
            }
    
    def record_performance_metric(self, metric_type: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        st.session_state.analytics_data['performance_metrics'].append(asdict(metric))
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(st.session_state.analytics_data['performance_metrics']) > 1000:
            st.session_state.analytics_data['performance_metrics'] = \
                st.session_state.analytics_data['performance_metrics'][-1000:]
    
    def record_processing_event(self, event_type: str, page_number: int, 
                              processing_mode: str, duration: float, 
                              success: bool, result_count: int, 
                              confidence_avg: float, metadata: Dict[str, Any] = None):
        """Record a processing event"""
        event = ProcessingEvent(
            timestamp=time.time(),
            event_type=event_type,
            page_number=page_number,
            processing_mode=processing_mode,
            duration=duration,
            success=success,
            result_count=result_count,
            confidence_avg=confidence_avg,
            metadata=metadata or {}
        )
        
        st.session_state.analytics_data['processing_events'].append(asdict(event))
        
        # Performance tracking
        self.record_performance_metric('processing_duration', duration, {
            'mode': processing_mode,
            'page': page_number,
            'success': success
        })
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            if not PSUTIL_AVAILABLE:
                # Return mock metrics when psutil not available
                return {
                    'timestamp': time.time(),
                    'cpu_percent': 0.0,
                    'memory_percent': 0.0,
                    'memory_used_gb': 0.0,
                    'memory_available_gb': 0.0,
                    'disk_percent': 0.0,
                    'disk_used_gb': 0.0,
                    'disk_free_gb': 0.0
                }
                
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_free_gb': disk.free / (1024**3)
            }
            
            return metrics
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {'timestamp': time.time(), 'error': str(e)}
    
    def render_analytics_dashboard(self):
        """Render the complete analytics dashboard"""
        if not STREAMLIT_AVAILABLE:
            logging.warning("Streamlit not available - UI components disabled")
            return
            
        st.markdown("# 📊 Analytics Dashboard")
        
        # Real-time metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            processing_events = st.session_state.analytics_data['processing_events']
            total_events = len(processing_events)
            st.metric("Total Operations", total_events)
        
        with col2:
            if processing_events:
                success_rate = sum(1 for e in processing_events if e['success']) / len(processing_events)
                st.metric("Success Rate", f"{success_rate:.1%}")
            else:
                st.metric("Success Rate", "N/A")
        
        with col3:
            if processing_events:
                avg_duration = sum(e['duration'] for e in processing_events) / len(processing_events)
                st.metric("Avg Duration", f"{avg_duration:.2f}s")
            else:
                st.metric("Avg Duration", "N/A")
        
        with col4:
            session_duration = time.time() - st.session_state.session_start_time
            st.metric("Session Time", f"{session_duration/60:.1f}m")
        
        # System performance
        with st.expander("🖥️ System Performance", expanded=False):
            system_metrics = self.get_system_metrics()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("CPU Usage", f"{system_metrics.get('cpu_percent', 0):.1f}%")
                st.metric("Memory Usage", f"{system_metrics.get('memory_percent', 0):.1f}%")
            
            with col2:
                memory_used = system_metrics.get('memory_used_gb', 0)
                memory_available = system_metrics.get('memory_available_gb', 0)
                st.metric("Memory Used", f"{memory_used:.1f} GB")
                st.metric("Memory Available", f"{memory_available:.1f} GB")
            
            with col3:
                disk_percent = system_metrics.get('disk_percent', 0)
                disk_free = system_metrics.get('disk_free_gb', 0)
                st.metric("Disk Usage", f"{disk_percent:.1f}%")
                st.metric("Disk Free", f"{disk_free:.1f} GB")
        
        # Processing analytics
        self._render_processing_analytics()
        
        # Performance trends
        self._render_performance_trends()
        
        # Quality metrics
        self._render_quality_metrics()
        
        # Export analytics
        self._render_export_options()
    
    def _render_processing_analytics(self):
        """Render processing-specific analytics"""
        with st.expander("🧠 Processing Analytics", expanded=True):
            processing_events = st.session_state.analytics_data['processing_events']
            
            if not processing_events:
                st.info("No processing events recorded yet")
                return
            
            if PANDAS_AVAILABLE and PLOTLY_AVAILABLE:
                df = pd.DataFrame(processing_events)
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Processing mode distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    mode_counts = df['processing_mode'].value_counts()
                    fig = px.pie(
                        values=mode_counts.values,
                        names=mode_counts.index,
                        title="Processing Mode Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Success rate by mode
                    success_by_mode = df.groupby('processing_mode')['success'].mean()
                    fig = px.bar(
                        x=success_by_mode.index,
                        y=success_by_mode.values,
                        title="Success Rate by Processing Mode",
                        labels={'y': 'Success Rate', 'x': 'Processing Mode'}
                    )
                    fig.update_layout(yaxis_tickformat='.1%')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Processing time trends
                if len(df) > 1:
                    fig = px.line(
                        df, 
                        x='datetime', 
                        y='duration',
                        color='processing_mode',
                        title="Processing Duration Over Time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Results quality
                fig = px.scatter(
                    df,
                    x='duration',
                    y='confidence_avg',
                    color='processing_mode',
                    size='result_count',
                    title="Processing Quality vs Duration",
                    labels={
                        'duration': 'Processing Duration (s)',
                        'confidence_avg': 'Average Confidence'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Fallback statistics without visualizations
                st.markdown("**Processing Statistics:**")
                
                # Group by processing mode
                mode_stats = {}
                for event in processing_events:
                    mode = event['processing_mode']
                    if mode not in mode_stats:
                        mode_stats[mode] = {
                            'count': 0,
                            'total_duration': 0,
                            'successes': 0,
                            'total_confidence': 0,
                            'total_results': 0
                        }
                    
                    stats = mode_stats[mode]
                    stats['count'] += 1
                    stats['total_duration'] += event['duration']
                    stats['successes'] += 1 if event['success'] else 0
                    stats['total_confidence'] += event['confidence_avg']
                    stats['total_results'] += event['result_count']
                
                for mode, stats in mode_stats.items():
                    with st.container():
                        st.markdown(f"**{mode}:**")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Operations", stats['count'])
                        with col2:
                            success_rate = stats['successes'] / stats['count']
                            st.metric("Success Rate", f"{success_rate:.1%}")
                        with col3:
                            avg_duration = stats['total_duration'] / stats['count']
                            st.metric("Avg Duration", f"{avg_duration:.2f}s")
                        with col4:
                            avg_confidence = stats['total_confidence'] / stats['count']
                            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    def _render_performance_trends(self):
        """Render performance trend analytics"""
        with st.expander("⚡ Performance Trends", expanded=False):
            performance_metrics = st.session_state.analytics_data['performance_metrics']
            
            if not performance_metrics:
                st.info("No performance metrics recorded yet")
                return
            
            if PANDAS_AVAILABLE and PLOTLY_AVAILABLE:
                df = pd.DataFrame(performance_metrics)
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Performance over time
                metric_types = df['metric_type'].unique()
                
                if len(metric_types) > 0:
                    selected_metrics = st.multiselect(
                        "Select metrics to display",
                        metric_types,
                        default=metric_types[:3] if len(metric_types) > 3 else metric_types
                    )
                    
                    if selected_metrics:
                        filtered_df = df[df['metric_type'].isin(selected_metrics)]
                        
                        fig = px.line(
                            filtered_df,
                            x='datetime',
                            y='value',
                            color='metric_type',
                            title="Performance Metrics Over Time"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Performance statistics
                        st.markdown("**Performance Statistics:**")
                        
                        for metric_type in selected_metrics:
                            metric_data = df[df['metric_type'] == metric_type]['value']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(f"{metric_type} - Mean", f"{metric_data.mean():.3f}")
                            with col2:
                                st.metric(f"{metric_type} - Median", f"{metric_data.median():.3f}")
                            with col3:
                                st.metric(f"{metric_type} - Min", f"{metric_data.min():.3f}")
                            with col4:
                                st.metric(f"{metric_type} - Max", f"{metric_data.max():.3f}")
            
            else:
                # Fallback without visualizations
                metric_summary = {}
                for metric in performance_metrics:
                    metric_type = metric['metric_type']
                    if metric_type not in metric_summary:
                        metric_summary[metric_type] = []
                    metric_summary[metric_type].append(metric['value'])
                
                for metric_type, values in metric_summary.items():
                    st.markdown(f"**{metric_type}:**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Count", len(values))
                    with col2:
                        st.metric("Average", f"{sum(values)/len(values):.3f}")
                    with col3:
                        st.metric("Min", f"{min(values):.3f}")
                    with col4:
                        st.metric("Max", f"{max(values):.3f}")
    
    def _render_quality_metrics(self):
        """Render quality and accuracy metrics"""
        with st.expander("🎯 Quality Metrics", expanded=False):
            processing_events = st.session_state.analytics_data['processing_events']
            
            if not processing_events:
                st.info("No quality data available yet")
                return
            
            # Calculate quality metrics
            total_results = sum(e['result_count'] for e in processing_events)
            total_confidence = sum(e['confidence_avg'] * e['result_count'] for e in processing_events)
            
            if total_results > 0:
                overall_confidence = total_confidence / total_results
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Results Generated", total_results)
                
                with col2:
                    st.metric("Overall Confidence", f"{overall_confidence:.1%}")
                
                with col3:
                    high_quality_results = sum(1 for e in processing_events 
                                             if e['confidence_avg'] > 0.8)
                    quality_rate = high_quality_results / len(processing_events)
                    st.metric("High Quality Rate", f"{quality_rate:.1%}")
                
                # Quality distribution
                if PLOTLY_AVAILABLE:
                    confidence_values = [e['confidence_avg'] for e in processing_events]
                    
                    fig = px.histogram(
                        x=confidence_values,
                        nbins=20,
                        title="Confidence Score Distribution",
                        labels={'x': 'Confidence Score', 'y': 'Frequency'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    def _render_export_options(self):
        """Render analytics export options"""
        with st.expander("📤 Export Analytics", expanded=False):
            st.markdown("**Export Options:**")
            
            export_format = st.selectbox(
                "Export Format",
                ["JSON", "CSV", "Summary Report"],
                key="analytics_export_format"
            )
            
            if st.button("📥 Export Analytics Data"):
                self._export_analytics_data(export_format)
    
    def _export_analytics_data(self, format_type: str):
        """Export analytics data in specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "JSON":
                data = {
                    "session_info": {
                        "session_id": st.session_state.analytics_session_id,
                        "export_timestamp": datetime.now().isoformat(),
                        "session_duration": time.time() - st.session_state.session_start_time
                    },
                    "analytics_data": st.session_state.analytics_data
                }
                
                content = json.dumps(data, indent=2)
                filename = f"analytics_data_{timestamp}.json"
                mime_type = "application/json"
                
            elif format_type == "CSV" and PANDAS_AVAILABLE:
                # Export processing events as CSV
                processing_events = st.session_state.analytics_data['processing_events']
                
                if processing_events:
                    df = pd.DataFrame(processing_events)
                    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                    content = df.to_csv(index=False)
                    filename = f"processing_events_{timestamp}.csv"
                    mime_type = "text/csv"
                else:
                    st.warning("No processing events to export")
                    return
                    
            else:  # Summary Report
                content = self._generate_summary_report()
                filename = f"analytics_summary_{timestamp}.md"
                mime_type = "text/markdown"
            
            st.download_button(
                label=f"📥 Download {format_type}",
                data=content,
                file_name=filename,
                mime=mime_type
            )
            
            st.success("✅ Analytics export ready!")
            
        except Exception as e:
            logger.error(f"Analytics export error: {e}")
            st.error(f"Export failed: {str(e)}")
    
    def _generate_summary_report(self) -> str:
        """Generate a summary report of analytics"""
        processing_events = st.session_state.analytics_data['processing_events']
        performance_metrics = st.session_state.analytics_data['performance_metrics']
        
        session_duration = time.time() - st.session_state.session_start_time
        
        report = f"""# Analytics Summary Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Session ID: {st.session_state.analytics_session_id}
Session Duration: {session_duration/60:.1f} minutes

## Overview

- **Total Processing Operations:** {len(processing_events)}
- **Performance Metrics Recorded:** {len(performance_metrics)}
- **Session Duration:** {session_duration/60:.1f} minutes

"""
        
        if processing_events:
            # Processing statistics
            total_results = sum(e['result_count'] for e in processing_events)
            successful_operations = sum(1 for e in processing_events if e['success'])
            success_rate = successful_operations / len(processing_events)
            
            avg_duration = sum(e['duration'] for e in processing_events) / len(processing_events)
            avg_confidence = sum(e['confidence_avg'] for e in processing_events) / len(processing_events)
            
            report += f"""## Processing Performance

- **Success Rate:** {success_rate:.1%}
- **Average Processing Time:** {avg_duration:.2f} seconds
- **Total Results Generated:** {total_results}
- **Average Confidence:** {avg_confidence:.1%}

"""
            
            # Processing mode breakdown
            mode_stats = {}
            for event in processing_events:
                mode = event['processing_mode']
                if mode not in mode_stats:
                    mode_stats[mode] = {'count': 0, 'duration': 0, 'results': 0}
                mode_stats[mode]['count'] += 1
                mode_stats[mode]['duration'] += event['duration']
                mode_stats[mode]['results'] += event['result_count']
            
            report += "## Processing Mode Statistics\n\n"
            for mode, stats in mode_stats.items():
                avg_duration_mode = stats['duration'] / stats['count']
                report += f"**{mode}:**\n"
                report += f"- Operations: {stats['count']}\n"
                report += f"- Average Duration: {avg_duration_mode:.2f}s\n"
                report += f"- Total Results: {stats['results']}\n\n"
        
        # System performance
        if performance_metrics:
            report += "## System Performance\n\n"
            
            metric_types = set(m['metric_type'] for m in performance_metrics)
            for metric_type in metric_types:
                values = [m['value'] for m in performance_metrics if m['metric_type'] == metric_type]
                report += f"**{metric_type}:**\n"
                report += f"- Count: {len(values)}\n"
                report += f"- Average: {sum(values)/len(values):.3f}\n"
                report += f"- Min: {min(values):.3f}\n"
                report += f"- Max: {max(values):.3f}\n\n"
        
        report += f"""
---

*Report generated by Universal Document Reader & AI Processor Analytics Dashboard*
"""
        
        return report
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session analytics"""
        processing_events = st.session_state.analytics_data['processing_events']
        performance_metrics = st.session_state.analytics_data['performance_metrics']
        
        summary = {
            'session_id': st.session_state.analytics_session_id,
            'session_duration': time.time() - st.session_state.session_start_time,
            'total_operations': len(processing_events),
            'total_metrics': len(performance_metrics),
            'success_rate': 0,
            'average_confidence': 0,
            'average_duration': 0
        }
        
        if processing_events:
            successful = sum(1 for e in processing_events if e['success'])
            summary['success_rate'] = successful / len(processing_events)
            summary['average_confidence'] = sum(e['confidence_avg'] for e in processing_events) / len(processing_events)
            summary['average_duration'] = sum(e['duration'] for e in processing_events) / len(processing_events)
        
        return summary