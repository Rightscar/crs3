"""
Export Center UI
================

Interface for exporting characters and training data.
"""

import streamlit as st
from datetime import datetime

from services.export_service import ExportService
from integrations.adapters.analytics_adapter import AnalyticsAdapter
from config.logging_config import logger
from core.exceptions import StorageError


def render_export_center():
    """Render the export center page"""
    st.markdown("## 📤 Export Center")
    st.markdown("Export your characters in various formats for sharing, backup, or AI training.")
    
    # Initialize services
    export_service = ExportService()
    analytics = AnalyticsAdapter()
    
    # Export tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎭 Character Export",
        "🤖 Training Data",
        "🎨 Character Cards",
        "📊 Analytics Reports"
    ])
    
    with tab1:
        render_character_export(export_service)
    
    with tab2:
        render_training_data_export(export_service)
    
    with tab3:
        render_character_cards(export_service)
    
    with tab4:
        render_analytics_export(analytics)


def render_character_export(export_service: ExportService):
    """Render character export section"""
    st.markdown("### Export Characters")
    st.markdown("Export individual characters or your entire collection.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Export mode
        export_mode = st.radio(
            "Export Mode",
            ["Single Character", "All Characters", "Search Results"],
            horizontal=True
        )
        
        if export_mode == "Single Character":
            # Get character list
            characters = st.session_state.get('extracted_characters', [])
            if characters:
                character_names = [char['name'] for char in characters]
                selected_char = st.selectbox(
                    "Select Character",
                    character_names
                )
                
                # Find selected character
                character = next(
                    (char for char in characters if char['name'] == selected_char),
                    None
                )
            else:
                st.warning("No characters available. Create some characters first!")
                character = None
        
        elif export_mode == "Search Results":
            search_query = st.text_input(
                "Search Characters",
                placeholder="Enter character name or traits..."
            )
        
        # Export format
        formats = export_service.get_export_formats()
        format_names = [f"{fmt['name']} (.{fmt['format']})" for fmt in formats]
        selected_format_idx = st.selectbox(
            "Export Format",
            range(len(formats)),
            format_func=lambda x: format_names[x]
        )
        selected_format = formats[selected_format_idx]['format']
        
        # Additional options
        include_analytics = st.checkbox(
            "Include Analytics Data",
            help="Add performance metrics and usage statistics"
        )
    
    with col2:
        # Format description
        st.info(formats[selected_format_idx]['description'])
        
        # Export button
        if st.button("🚀 Export", type="primary", use_container_width=True):
            try:
                with st.spinner("Exporting..."):
                    if export_mode == "Single Character" and character:
                        result = export_service.export_character(
                            character['id'],
                            format=selected_format,
                            include_analytics=include_analytics
                        )
                        
                        if result['success']:
                            st.success(f"✅ Exported to: {result['file_path']}")
                            
                            # Offer download
                            with open(result['file_path'], 'rb') as f:
                                st.download_button(
                                    "📥 Download",
                                    f.read(),
                                    file_name=result['file_path'].split('/')[-1],
                                    mime=get_mime_type(selected_format)
                                )
                    
                    elif export_mode == "All Characters":
                        result = export_service.export_all_characters(
                            format=selected_format
                        )
                        
                        if result['success']:
                            st.success(f"✅ Exported {result['exported_count']} characters")
                    
                    elif export_mode == "Search Results" and search_query:
                        result = export_service.export_all_characters(
                            format=selected_format,
                            search_query=search_query
                        )
                        
                        if result['success']:
                            st.success(f"✅ Exported {result['exported_count']} matching characters")
                    
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")


def render_training_data_export(export_service: ExportService):
    """Render training data export section"""
    st.markdown("### Export Training Data")
    st.markdown("Prepare your characters for fine-tuning AI models.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Model selection
        model_types = export_service.get_model_types()
        model_names = [mt['name'] for mt in model_types]
        selected_model_idx = st.selectbox(
            "Target Model",
            range(len(model_types)),
            format_func=lambda x: model_names[x]
        )
        selected_model = model_types[selected_model_idx]['type']
        
        # Character selection
        character_selection = st.radio(
            "Characters to Include",
            ["All Characters", "Selected Characters"],
            horizontal=True
        )
        
        selected_char_ids = []
        if character_selection == "Selected Characters":
            characters = st.session_state.get('extracted_characters', [])
            if characters:
                selected_chars = st.multiselect(
                    "Select Characters",
                    [char['name'] for char in characters]
                )
                
                # Get IDs of selected characters
                selected_char_ids = [
                    char['id'] for char in characters 
                    if char['name'] in selected_chars
                ]
        
        # Format (usually JSONL for training)
        format = st.selectbox(
            "Export Format",
            ["jsonl", "json"],
            help="JSONL is recommended for model fine-tuning"
        )
    
    with col2:
        # Model description
        st.info(model_types[selected_model_idx]['description'])
        
        # Training tips
        with st.expander("💡 Training Tips"):
            st.markdown("""
            - **GPT**: Use at least 50-100 examples per character
            - **Claude**: Focus on diverse conversation scenarios
            - **Quality > Quantity**: Better examples lead to better results
            - **Test First**: Try with a small dataset before full training
            """)
    
    # Export button
    if st.button("🤖 Generate Training Data", type="primary"):
        try:
            with st.spinner("Generating training data..."):
                result = export_service.export_training_data(
                    character_ids=selected_char_ids if selected_char_ids else None,
                    model_type=selected_model,
                    format=format
                )
                
                if result['success']:
                    st.success(f"✅ Generated {result['num_examples']} training examples")
                    st.info(f"📁 Saved to: {result['file_path']}")
                    
                    # Show sample
                    with st.expander("View Sample"):
                        # Would show first few examples
                        st.code("Sample training data would appear here")
                        
        except Exception as e:
            st.error(f"❌ Failed to generate training data: {str(e)}")


def render_character_cards(export_service: ExportService):
    """Render character card creation section"""
    st.markdown("### Create Character Cards")
    st.markdown("Generate beautiful shareable cards for your characters.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Character selection
        characters = st.session_state.get('extracted_characters', [])
        if characters:
            character_names = [char['name'] for char in characters]
            selected_char_name = st.selectbox(
                "Select Character",
                character_names
            )
            
            # Find selected character
            character = next(
                (char for char in characters if char['name'] == selected_char_name),
                None
            )
            
            # Template selection
            templates = [
                "Default",
                "Minimal",
                "Detailed",
                "Social Media",
                "Trading Card"
            ]
            selected_template = st.selectbox(
                "Card Template",
                templates
            ).lower().replace(" ", "_")
            
        else:
            st.warning("No characters available!")
            character = None
    
    with col2:
        # Preview area
        st.markdown("#### Preview")
        if character:
            # Simple preview
            st.markdown(f"""
            <div style='border: 2px solid #ddd; padding: 20px; border-radius: 10px;'>
                <h3>{character['avatar']} {character['name']}</h3>
                <p><strong>{character['role']}</strong></p>
                <p>{character['description'][:100]}...</p>
                <hr>
                <small>Performance Score: ⭐⭐⭐⭐</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Create card button
    if st.button("🎨 Create Card", type="primary") and character:
        try:
            with st.spinner("Creating character card..."):
                result = export_service.export_character_card(
                    character['id'],
                    template=selected_template
                )
                
                if result['success']:
                    st.success("✅ Character card created!")
                    
                    # Offer download
                    with open(result['file_path'], 'rb') as f:
                        st.download_button(
                            "📥 Download Card",
                            f.read(),
                            file_name=f"{character['name']}_card.{result['format']}",
                            mime=get_mime_type(result['format'])
                        )
                        
        except Exception as e:
            st.error(f"❌ Failed to create card: {str(e)}")


def render_analytics_export(analytics: AnalyticsAdapter):
    """Render analytics export section"""
    st.markdown("### Export Analytics Reports")
    st.markdown("Generate comprehensive analytics reports.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Report type
        report_types = [
            ("Summary Report", "summary"),
            ("Detailed Analytics", "detailed"),
            ("Character Performance", "character"),
            ("User Engagement", "user")
        ]
        
        report_type = st.selectbox(
            "Report Type",
            [rt[1] for rt in report_types],
            format_func=lambda x: next(rt[0] for rt in report_types if rt[1] == x)
        )
        
        # Time range
        time_ranges = [
            ("Last 7 Days", 7),
            ("Last 30 Days", 30),
            ("Last 90 Days", 90),
            ("All Time", 365)
        ]
        
        selected_range = st.selectbox(
            "Time Range",
            [tr[1] for tr in time_ranges],
            format_func=lambda x: next(tr[0] for tr in time_ranges if tr[1] == x)
        )
        
        # Format
        report_format = st.selectbox(
            "Export Format",
            ["json", "html", "pdf"],
            help="HTML and PDF include visualizations"
        )
    
    with col2:
        # Report info
        st.info("""
        **Reports Include:**
        - Character performance metrics
        - User engagement statistics
        - Usage patterns and trends
        - Recommendations
        """)
    
    # Generate report button
    if st.button("📊 Generate Report", type="primary"):
        try:
            with st.spinner("Generating analytics report..."):
                from datetime import timedelta
                
                result = analytics.generate_analytics_report(
                    report_type=report_type,
                    time_range=timedelta(days=selected_range),
                    format=report_format
                )
                
                if result['success']:
                    st.success("✅ Report generated successfully!")
                    
                    # Show summary
                    if 'data' in result:
                        with st.expander("Report Summary"):
                            st.json(result['data']['metrics'])
                            
        except Exception as e:
            st.error(f"❌ Failed to generate report: {str(e)}")


def get_mime_type(format: str) -> str:
    """Get MIME type for file format"""
    mime_types = {
        'json': 'application/json',
        'jsonl': 'application/jsonl',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'csv': 'text/csv',
        'txt': 'text/plain',
        'html': 'text/html'
    }
    return mime_types.get(format, 'application/octet-stream')