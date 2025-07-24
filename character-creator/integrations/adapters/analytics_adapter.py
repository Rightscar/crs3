"""Analytics adapter for analytics_dashboard module"""

import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

# Add modules path to system path
sys.path.insert(0, '/workspace/modules')

from ..config import integration_config

logger = logging.getLogger(__name__)

class AnalyticsAdapter:
    """Adapter for the existing analytics_dashboard module"""
    
    def __init__(self):
        """Initialize the analytics adapter"""
        self._initialized = False
        self.dashboard = None
        self.visual_dashboard = None
        
        try:
            from analytics_dashboard import AnalyticsDashboard
            self.dashboard = AnalyticsDashboard()
            self._initialized = True
            logger.info("AnalyticsDashboard initialized successfully")
            
            # Try to import visual dashboard too
            try:
                from visual_dashboard import VisualDashboard
                self.visual_dashboard = VisualDashboard()
                logger.info("VisualDashboard initialized successfully")
            except ImportError:
                logger.warning("VisualDashboard not available")
                
        except ImportError as e:
            logger.error(f"Failed to import AnalyticsDashboard: {e}")
            self._initialized = False
        except Exception as e:
            logger.error(f"Error initializing AnalyticsDashboard: {e}")
            self._initialized = False
    
    def track_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Track an analytics event
        
        Args:
            event_type: Type of event (e.g., 'character_created', 'chat_started')
            event_data: Event-specific data
            user_id: Optional user identifier
            
        Returns:
            Success status
        """
        try:
            event = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id or 'anonymous',
                'data': event_data
            }
            
            if self._initialized and hasattr(self.dashboard, 'track_event'):
                self.dashboard.track_event(event)
            else:
                # Fallback: log the event
                logger.info(f"Analytics event: {event}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False
    
    def get_character_analytics(
        self,
        character_id: str,
        time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific character
        
        Args:
            character_id: Character identifier
            time_range: Optional time range for analytics
            
        Returns:
            Analytics data
        """
        if not self._initialized:
            return self._get_default_analytics()
        
        try:
            if hasattr(self.dashboard, 'get_character_analytics'):
                return self.dashboard.get_character_analytics(
                    character_id,
                    time_range or timedelta(days=30)
                )
            else:
                # Generate basic analytics
                return {
                    'character_id': character_id,
                    'total_chats': 0,
                    'total_messages': 0,
                    'average_session_length': 0,
                    'user_satisfaction': 0,
                    'engagement_score': 0,
                    'time_range': str(time_range or timedelta(days=30))
                }
                
        except Exception as e:
            logger.error(f"Error getting character analytics: {e}")
            return self._get_default_analytics()
    
    def get_user_engagement_metrics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get user engagement metrics
        
        Args:
            user_id: Optional user identifier
            time_range: Optional time range
            
        Returns:
            Engagement metrics
        """
        if not self._initialized:
            return self._get_default_engagement_metrics()
        
        try:
            if hasattr(self.dashboard, 'get_user_engagement'):
                return self.dashboard.get_user_engagement(
                    user_id,
                    time_range or timedelta(days=7)
                )
            else:
                return self._get_default_engagement_metrics()
                
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return self._get_default_engagement_metrics()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get overall system metrics
        
        Returns:
            System metrics
        """
        if not self._initialized:
            return self._get_default_system_metrics()
        
        try:
            if hasattr(self.dashboard, 'get_system_metrics'):
                return self.dashboard.get_system_metrics()
            else:
                return self._get_default_system_metrics()
                
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return self._get_default_system_metrics()
    
    def generate_analytics_report(
        self,
        report_type: str = 'summary',
        time_range: Optional[timedelta] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Generate analytics report
        
        Args:
            report_type: Type of report ('summary', 'detailed', 'character', 'user')
            time_range: Time range for report
            format: Output format ('json', 'html', 'pdf')
            
        Returns:
            Report data or file path
        """
        if not self._initialized:
            return {
                'success': False,
                'error': 'Analytics not initialized'
            }
        
        try:
            report_data = {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'time_range': str(time_range or timedelta(days=30)),
                'metrics': {}
            }
            
            # Gather metrics based on report type
            if report_type == 'summary':
                report_data['metrics'] = {
                    'system': self.get_system_metrics(),
                    'engagement': self.get_user_engagement_metrics(time_range=time_range),
                    'top_characters': self._get_top_characters()
                }
            elif report_type == 'detailed':
                report_data['metrics'] = {
                    'system': self.get_system_metrics(),
                    'engagement': self.get_user_engagement_metrics(time_range=time_range),
                    'characters': self._get_all_character_analytics(time_range),
                    'usage_patterns': self._get_usage_patterns()
                }
            
            # Format report
            if format == 'html' and self.visual_dashboard:
                return self.visual_dashboard.generate_html_report(report_data)
            elif format == 'pdf' and self.visual_dashboard:
                return self.visual_dashboard.generate_pdf_report(report_data)
            else:
                return {
                    'success': True,
                    'data': report_data
                }
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_character_performance_metrics(
        self,
        character_id: str
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a character
        
        Args:
            character_id: Character identifier
            
        Returns:
            Performance metrics
        """
        analytics = self.get_character_analytics(character_id)
        
        # Calculate performance scores
        engagement_score = analytics.get('engagement_score', 0)
        satisfaction_score = analytics.get('user_satisfaction', 0)
        retention_rate = analytics.get('retention_rate', 0)
        
        performance_score = (engagement_score + satisfaction_score + retention_rate) / 3
        
        return {
            'character_id': character_id,
            'performance_score': round(performance_score, 2),
            'engagement_score': engagement_score,
            'satisfaction_score': satisfaction_score,
            'retention_rate': retention_rate,
            'recommendations': self._get_performance_recommendations(performance_score)
        }
    
    def track_character_interaction(
        self,
        character_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """
        Track character interaction
        
        Args:
            character_id: Character identifier
            interaction_type: Type of interaction
            interaction_data: Interaction details
            
        Returns:
            Success status
        """
        return self.track_event(
            f'character_{interaction_type}',
            {
                'character_id': character_id,
                **interaction_data
            }
        )
    
    def _get_default_analytics(self) -> Dict[str, Any]:
        """Get default analytics when not initialized"""
        return {
            'total_chats': 0,
            'total_messages': 0,
            'average_session_length': 0,
            'user_satisfaction': 0,
            'engagement_score': 0
        }
    
    def _get_default_engagement_metrics(self) -> Dict[str, Any]:
        """Get default engagement metrics"""
        return {
            'active_users': 0,
            'total_sessions': 0,
            'average_session_duration': 0,
            'messages_per_session': 0,
            'return_rate': 0
        }
    
    def _get_default_system_metrics(self) -> Dict[str, Any]:
        """Get default system metrics"""
        return {
            'total_characters': 0,
            'total_users': 0,
            'total_conversations': 0,
            'total_messages': 0,
            'system_uptime': 0,
            'api_response_time': 0
        }
    
    def _get_top_characters(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing characters"""
        # This would query actual data
        return []
    
    def _get_all_character_analytics(
        self,
        time_range: Optional[timedelta]
    ) -> Dict[str, Any]:
        """Get analytics for all characters"""
        # This would aggregate character data
        return {}
    
    def _get_usage_patterns(self) -> Dict[str, Any]:
        """Get usage patterns"""
        return {
            'peak_hours': [],
            'popular_features': [],
            'common_workflows': []
        }
    
    def _get_performance_recommendations(
        self,
        performance_score: float
    ) -> List[str]:
        """Get recommendations based on performance"""
        recommendations = []
        
        if performance_score < 0.3:
            recommendations.extend([
                "Consider updating character personality traits",
                "Add more engaging dialogue examples",
                "Review and improve character backstory"
            ])
        elif performance_score < 0.6:
            recommendations.extend([
                "Enhance character's unique behaviors",
                "Add more emotional depth",
                "Improve response variety"
            ])
        else:
            recommendations.extend([
                "Character is performing well",
                "Consider creating similar characters",
                "Share character as a template"
            ])
        
        return recommendations