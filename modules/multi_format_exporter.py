"""
Multi-Format Exporter Module
============================

Export generated dialogues to multiple formats: JSON, JSONL, CSV, Excel.
Provides clean, production-ready export functionality.

Features:
- JSON export with metadata
- JSONL export for training data
- CSV export for spreadsheet analysis
- Excel export with multiple sheets
- Batch export options
"""

import streamlit as st
import logging
import json
import csv
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiFormatExporter:
    """Export dialogues to multiple formats"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_to_json(self, dialogues: List[Dict[str, Any]], 
                      include_metadata: bool = True) -> str:
        """Export dialogues to JSON format"""
        
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_dialogues": len(dialogues),
                "export_format": "json"
            } if include_metadata else {},
            "dialogues": dialogues
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def export_to_jsonl(self, dialogues: List[Dict[str, Any]]) -> str:
        """Export dialogues to JSONL format (one JSON object per line)"""
        
        lines = []
        for dialogue in dialogues:
            # Create training data format
            training_item = {
                "messages": [
                    {"role": "user", "content": dialogue['question']},
                    {"role": "assistant", "content": dialogue['answer']}
                ],
                "metadata": {
                    "source_chunk": dialogue.get('source_chunk_id', ''),
                    "dialogue_type": dialogue.get('dialogue_type', ''),
                    "topics": dialogue.get('topics', [])
                }
            }
            lines.append(json.dumps(training_item, ensure_ascii=False))
        
        return '\n'.join(lines)
    
    def export_to_csv(self, dialogues: List[Dict[str, Any]]) -> str:
        """Export dialogues to CSV format"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Question', 'Answer', 'Source Chunk', 
            'Dialogue Type', 'Topics', 'Confidence'
        ])
        
        # Write data
        for dialogue in dialogues:
            writer.writerow([
                dialogue.get('id', ''),
                dialogue.get('question', ''),
                dialogue.get('answer', ''),
                dialogue.get('source_chunk_id', ''),
                dialogue.get('dialogue_type', ''),
                ', '.join(dialogue.get('topics', [])),
                dialogue.get('confidence', 0.8)
            ])
        
        return output.getvalue()
    
    def export_to_excel(self, dialogues: List[Dict[str, Any]]) -> bytes:
        """Export dialogues to Excel format with multiple sheets"""
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Main dialogues sheet
            df_dialogues = pd.DataFrame([
                {
                    'ID': d.get('id', ''),
                    'Question': d.get('question', ''),
                    'Answer': d.get('answer', ''),
                    'Source Chunk': d.get('source_chunk_id', ''),
                    'Dialogue Type': d.get('dialogue_type', ''),
                    'Topics': ', '.join(d.get('topics', [])),
                    'Confidence': d.get('confidence', 0.8)
                }
                for d in dialogues
            ])
            df_dialogues.to_excel(writer, sheet_name='Dialogues', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Dialogues',
                    'Average Confidence',
                    'Unique Source Chunks',
                    'Most Common Dialogue Type',
                    'Export Timestamp'
                ],
                'Value': [
                    len(dialogues),
                    sum(d.get('confidence', 0.8) for d in dialogues) / len(dialogues) if dialogues else 0,
                    len(set(d.get('source_chunk_id', '') for d in dialogues)),
                    max(set(d.get('dialogue_type', '') for d in dialogues), 
                        key=lambda x: sum(1 for d in dialogues if d.get('dialogue_type') == x)) if dialogues else '',
                    datetime.now().isoformat()
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Topics analysis sheet
            all_topics = []
            for d in dialogues:
                all_topics.extend(d.get('topics', []))
            
            if all_topics:
                topic_counts = pd.Series(all_topics).value_counts()
                df_topics = pd.DataFrame({
                    'Topic': topic_counts.index,
                    'Count': topic_counts.values
                })
                df_topics.to_excel(writer, sheet_name='Topics', index=False)
        
        return output.getvalue()
    
    def create_export_package(self, dialogues: List[Dict[str, Any]], 
                             formats: List[str] = None) -> bytes:
        """Create a ZIP package with multiple export formats"""
        
        if formats is None:
            formats = ['json', 'jsonl', 'csv', 'excel']
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Add JSON export
            if 'json' in formats:
                json_content = self.export_to_json(dialogues)
                zip_file.writestr(f'dialogues_{self.timestamp}.json', json_content)
            
            # Add JSONL export
            if 'jsonl' in formats:
                jsonl_content = self.export_to_jsonl(dialogues)
                zip_file.writestr(f'training_data_{self.timestamp}.jsonl', jsonl_content)
            
            # Add CSV export
            if 'csv' in formats:
                csv_content = self.export_to_csv(dialogues)
                zip_file.writestr(f'dialogues_{self.timestamp}.csv', csv_content)
            
            # Add Excel export
            if 'excel' in formats:
                excel_content = self.export_to_excel(dialogues)
                zip_file.writestr(f'dialogues_{self.timestamp}.xlsx', excel_content)
            
            # Add README
            readme_content = self._create_readme(dialogues, formats)
            zip_file.writestr('README.txt', readme_content)
        
        return zip_buffer.getvalue()
    
    def _create_readme(self, dialogues: List[Dict[str, Any]], formats: List[str]) -> str:
        """Create README file for export package"""
        
        readme = f"""
DIALOGUE EXPORT PACKAGE
======================

Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Dialogues: {len(dialogues)}
Export Formats: {', '.join(formats)}

FILE DESCRIPTIONS:
-----------------

"""
        
        if 'json' in formats:
            readme += f"""
• dialogues_{self.timestamp}.json
  Complete dialogue data in JSON format with metadata
  Use for: Data analysis, backup, general processing

"""
        
        if 'jsonl' in formats:
            readme += f"""
• training_data_{self.timestamp}.jsonl
  Training data format (one JSON object per line)
  Use for: AI model fine-tuning, machine learning

"""
        
        if 'csv' in formats:
            readme += f"""
• dialogues_{self.timestamp}.csv
  Comma-separated values format
  Use for: Spreadsheet analysis, data visualization

"""
        
        if 'excel' in formats:
            readme += f"""
• dialogues_{self.timestamp}.xlsx
  Excel workbook with multiple sheets:
  - Dialogues: Main data
  - Summary: Statistics and metrics
  - Topics: Topic analysis
  Use for: Advanced analysis, reporting, presentations

"""
        
        readme += """
DATA STRUCTURE:
--------------

Each dialogue contains:
- ID: Unique identifier
- Question: Generated question
- Answer: Generated answer
- Source Chunk: Original text chunk ID
- Dialogue Type: Style of dialogue (Q&A, Conversation, etc.)
- Topics: Associated topics
- Confidence: Quality confidence score

USAGE NOTES:
-----------

• JSONL format is optimized for AI training
• Excel format provides the most comprehensive analysis
• CSV format is best for simple data processing
• JSON format preserves all metadata

Generated by Universal Text-to-Dialogue AI System
"""
        
        return readme

def render_export_ui(dialogues: List[Dict[str, Any]]) -> None:
    """
    Render export interface for generated dialogues
    
    Args:
        dialogues: List of dialogue dictionaries
    """
    if not dialogues:
        st.warning("No dialogues available for export")
        return
    
    st.subheader("📦 Export Generated Dialogues")
    
    # Export summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Dialogues", len(dialogues))
    with col2:
        avg_confidence = sum(d.get('confidence', 0.8) for d in dialogues) / len(dialogues)
        st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    with col3:
        unique_chunks = len(set(d.get('source_chunk_id', '') for d in dialogues))
        st.metric("Source Chunks", unique_chunks)
    with col4:
        dialogue_types = set(d.get('dialogue_type', '') for d in dialogues)
        st.metric("Dialogue Types", len(dialogue_types))
    
    # Export options
    st.markdown("#### Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_formats = st.multiselect(
            "Select Export Formats",
            options=['JSON', 'JSONL', 'CSV', 'Excel'],
            default=['JSON', 'JSONL'],
            help="Choose which formats to include in export"
        )
    
    with col2:
        include_metadata = st.checkbox(
            "Include Metadata",
            value=True,
            help="Include export timestamp and summary information"
        )
    
    # Preview options
    st.markdown("#### Preview Data")
    
    preview_format = st.selectbox(
        "Preview Format",
        options=['Table', 'JSON', 'JSONL'],
        help="Choose how to preview the data"
    )
    
    # Show preview
    with st.expander("📋 Data Preview", expanded=True):
        if preview_format == 'Table':
            # Create DataFrame for display
            df = pd.DataFrame([
                {
                    'Question': d.get('question', '')[:100] + '...' if len(d.get('question', '')) > 100 else d.get('question', ''),
                    'Answer': d.get('answer', '')[:100] + '...' if len(d.get('answer', '')) > 100 else d.get('answer', ''),
                    'Type': d.get('dialogue_type', ''),
                    'Confidence': d.get('confidence', 0.8)
                }
                for d in dialogues[:10]  # Show first 10
            ])
            st.dataframe(df, use_container_width=True)
            
            if len(dialogues) > 10:
                st.info(f"Showing first 10 of {len(dialogues)} dialogues")
        
        elif preview_format == 'JSON':
            exporter = MultiFormatExporter()
            json_preview = exporter.export_to_json(dialogues[:3], include_metadata)
            st.code(json_preview, language='json')
            
            if len(dialogues) > 3:
                st.info(f"Showing first 3 of {len(dialogues)} dialogues")
        
        elif preview_format == 'JSONL':
            exporter = MultiFormatExporter()
            jsonl_preview = exporter.export_to_jsonl(dialogues[:3])
            st.code(jsonl_preview, language='json')
            
            if len(dialogues) > 3:
                st.info(f"Showing first 3 of {len(dialogues)} dialogues")
    
    # Export buttons
    st.markdown("#### Download Exports")
    
    exporter = MultiFormatExporter()
    
    # Individual format downloads
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'JSON' in export_formats:
            json_data = exporter.export_to_json(dialogues, include_metadata)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"dialogues_{exporter.timestamp}.json",
                mime="application/json"
            )
    
    with col2:
        if 'JSONL' in export_formats:
            jsonl_data = exporter.export_to_jsonl(dialogues)
            st.download_button(
                label="📝 Download JSONL",
                data=jsonl_data,
                file_name=f"training_data_{exporter.timestamp}.jsonl",
                mime="application/json"
            )
    
    with col3:
        if 'CSV' in export_formats:
            csv_data = exporter.export_to_csv(dialogues)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"dialogues_{exporter.timestamp}.csv",
                mime="text/csv"
            )
    
    with col4:
        if 'Excel' in export_formats:
            excel_data = exporter.export_to_excel(dialogues)
            st.download_button(
                label="📈 Download Excel",
                data=excel_data,
                file_name=f"dialogues_{exporter.timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Complete package download
    if len(export_formats) > 1:
        st.markdown("---")
        
        if st.button("📦 Download Complete Package (ZIP)", type="primary"):
            with st.spinner("Creating export package..."):
                formats_lower = [fmt.lower() for fmt in export_formats]
                zip_data = exporter.create_export_package(dialogues, formats_lower)
                
                st.download_button(
                    label="💾 Download ZIP Package",
                    data=zip_data,
                    file_name=f"dialogue_export_package_{exporter.timestamp}.zip",
                    mime="application/zip"
                )
                
                st.success("✅ Export package created successfully!")

@st.cache_data
def prepare_export_data(dialogues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prepare dialogue data for export (cached for performance)
    
    Args:
        dialogues: List of dialogue dictionaries
        
    Returns:
        Prepared export data
    """
    return {
        'dialogues': dialogues,
        'summary': {
            'total_count': len(dialogues),
            'avg_confidence': sum(d.get('confidence', 0.8) for d in dialogues) / len(dialogues) if dialogues else 0,
            'unique_chunks': len(set(d.get('source_chunk_id', '') for d in dialogues)),
            'dialogue_types': list(set(d.get('dialogue_type', '') for d in dialogues))
        }
    }

