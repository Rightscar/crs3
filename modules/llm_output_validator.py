"""
LLM Output Validator Module
Ensures generated dialogues have correct formatting and quality standards.
"""

import streamlit as st
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time
from enum import Enum

class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    """Result of validation check"""
    level: ValidationLevel
    message: str
    field: str
    suggestion: Optional[str] = None

@dataclass
class DialogueValidationReport:
    """Complete validation report for a dialogue"""
    is_valid: bool
    quality_score: float
    validation_results: List[ValidationResult]
    corrected_dialogue: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0

class LLMOutputValidator:
    """
    Comprehensive validator for LLM-generated dialogue outputs.
    Ensures correct formatting, quality, and adherence to standards.
    """
    
    def __init__(self):
        """Initialize the LLM output validator"""
        self.validation_rules = self._load_validation_rules()
        self.format_patterns = self._load_format_patterns()
        self.quality_thresholds = {
            'min_words': 10,
            'max_words': 2000,
            'min_exchanges': 2,
            'max_exchanges': 50,
            'min_quality_score': 0.7,
            'coherence_threshold': 0.6
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration"""
        return {
            'required_fields': ['question', 'answer'],
            'optional_fields': ['context', 'metadata', 'confidence'],
            'format_types': {
                'qa_pairs': {
                    'pattern': r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)',
                    'min_pairs': 1,
                    'max_pairs': 20
                },
                'dialogue': {
                    'pattern': r'(Speaker\s*\w*|Person\s*\w*|Teacher|Student|Interviewer|Expert):\s*(.+?)(?=\n(?:Speaker|Person|Teacher|Student|Interviewer|Expert):|$)',
                    'min_exchanges': 2,
                    'max_exchanges': 30
                },
                'conversation': {
                    'pattern': r'(\w+):\s*(.+?)(?=\n\w+:|$)',
                    'min_speakers': 2,
                    'max_speakers': 5
                }
            }
        }
    
    def _load_format_patterns(self) -> Dict[str, str]:
        """Load regex patterns for format validation"""
        return {
            'qa_format': r'Q:\s*.+?\s*A:\s*.+',
            'dialogue_format': r'(Speaker|Person|Teacher|Student|Interviewer|Expert)\s*\w*:\s*.+',
            'conversation_format': r'\w+:\s*.+',
            'json_format': r'^\s*\{.*\}\s*$',
            'speaker_label': r'^[A-Za-z][A-Za-z0-9\s]*:',
            'question_indicators': r'\?|what|how|why|when|where|who|which|can|could|would|should|do|does|did|is|are|was|were',
            'answer_indicators': r'because|since|therefore|thus|however|moreover|furthermore|in conclusion'
        }
    
    def validate_dialogue(self, dialogue_text: str, expected_format: str = "auto") -> DialogueValidationReport:
        """
        Validate a dialogue text for format and quality
        
        Args:
            dialogue_text: The dialogue text to validate
            expected_format: Expected format ("qa_pairs", "dialogue", "conversation", "auto")
            
        Returns:
            DialogueValidationReport with validation results
        """
        start_time = time.time()
        validation_results = []
        
        # Basic validation
        if not dialogue_text or not dialogue_text.strip():
            return DialogueValidationReport(
                is_valid=False,
                quality_score=0.0,
                validation_results=[ValidationResult(
                    ValidationLevel.CRITICAL,
                    "Empty dialogue text",
                    "content",
                    "Provide non-empty dialogue content"
                )],
                processing_time=time.time() - start_time
            )
        
        # Auto-detect format if needed
        if expected_format == "auto":
            expected_format = self._detect_format(dialogue_text)
        
        # Format validation
        format_results = self._validate_format(dialogue_text, expected_format)
        validation_results.extend(format_results)
        
        # Content quality validation
        quality_results = self._validate_content_quality(dialogue_text)
        validation_results.extend(quality_results)
        
        # Structure validation
        structure_results = self._validate_structure(dialogue_text, expected_format)
        validation_results.extend(structure_results)
        
        # Language and coherence validation
        coherence_results = self._validate_coherence(dialogue_text)
        validation_results.extend(coherence_results)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(dialogue_text, validation_results)
        
        # Determine if valid
        critical_issues = [r for r in validation_results if r.level == ValidationLevel.CRITICAL]
        is_valid = len(critical_issues) == 0 and quality_score >= self.quality_thresholds['min_quality_score']
        
        # Generate corrected version if needed
        corrected_dialogue = None
        if not is_valid:
            corrected_dialogue = self._attempt_correction(dialogue_text, validation_results)
        
        return DialogueValidationReport(
            is_valid=is_valid,
            quality_score=quality_score,
            validation_results=validation_results,
            corrected_dialogue=corrected_dialogue,
            processing_time=time.time() - start_time
        )
    
    def _detect_format(self, text: str) -> str:
        """Auto-detect the dialogue format"""
        text_lower = text.lower()
        
        # Check for Q&A format
        if re.search(r'q:\s*.+?\s*a:\s*.+', text_lower, re.DOTALL):
            return "qa_pairs"
        
        # Check for dialogue format with specific roles
        if re.search(r'(teacher|student|interviewer|expert):\s*.+', text_lower):
            return "dialogue"
        
        # Check for general conversation format
        if re.search(r'\w+:\s*.+', text):
            return "conversation"
        
        return "conversation"  # Default fallback
    
    def _validate_format(self, text: str, format_type: str) -> List[ValidationResult]:
        """Validate dialogue format"""
        results = []
        
        if format_type not in self.validation_rules['format_types']:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                f"Unknown format type: {format_type}",
                "format",
                "Use supported format: qa_pairs, dialogue, or conversation"
            ))
            return results
        
        format_config = self.validation_rules['format_types'][format_type]
        pattern = format_config['pattern']
        
        # Check if format pattern matches
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        
        if not matches:
            results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                f"No valid {format_type} format detected",
                "format",
                f"Ensure text follows {format_type} format pattern"
            ))
            return results
        
        # Validate count constraints
        if format_type == "qa_pairs":
            min_pairs = format_config.get('min_pairs', 1)
            max_pairs = format_config.get('max_pairs', 20)
            
            if len(matches) < min_pairs:
                results.append(ValidationResult(
                    ValidationLevel.CRITICAL,
                    f"Too few Q&A pairs: {len(matches)} (minimum: {min_pairs})",
                    "structure",
                    f"Add more Q&A pairs to reach minimum of {min_pairs}"
                ))
            elif len(matches) > max_pairs:
                results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    f"Too many Q&A pairs: {len(matches)} (maximum: {max_pairs})",
                    "structure",
                    f"Consider reducing to maximum of {max_pairs} pairs"
                ))
        
        elif format_type in ["dialogue", "conversation"]:
            min_exchanges = format_config.get('min_exchanges', 2)
            max_exchanges = format_config.get('max_exchanges', 30)
            
            if len(matches) < min_exchanges:
                results.append(ValidationResult(
                    ValidationLevel.CRITICAL,
                    f"Too few exchanges: {len(matches)} (minimum: {min_exchanges})",
                    "structure",
                    f"Add more exchanges to reach minimum of {min_exchanges}"
                ))
            elif len(matches) > max_exchanges:
                results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    f"Too many exchanges: {len(matches)} (maximum: {max_exchanges})",
                    "structure",
                    f"Consider reducing to maximum of {max_exchanges} exchanges"
                ))
        
        return results
    
    def _validate_content_quality(self, text: str) -> List[ValidationResult]:
        """Validate content quality"""
        results = []
        
        # Word count validation
        words = text.split()
        word_count = len(words)
        
        if word_count < self.quality_thresholds['min_words']:
            results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                f"Content too short: {word_count} words (minimum: {self.quality_thresholds['min_words']})",
                "length",
                "Add more content to meet minimum word requirement"
            ))
        elif word_count > self.quality_thresholds['max_words']:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                f"Content very long: {word_count} words (maximum: {self.quality_thresholds['max_words']})",
                "length",
                "Consider breaking into smaller dialogues"
            ))
        
        # Check for repetitive content
        unique_words = set(word.lower() for word in words if len(word) > 3)
        repetition_ratio = len(unique_words) / max(word_count, 1)
        
        if repetition_ratio < 0.3:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                f"High repetition detected (uniqueness: {repetition_ratio:.1%})",
                "quality",
                "Reduce repetitive content and add variety"
            ))
        
        # Check for meaningful content
        if len(text.strip()) < 50:
            results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "Content appears to be too brief for meaningful dialogue",
                "content",
                "Expand content to create substantial dialogue"
            ))
        
        return results
    
    def _validate_structure(self, text: str, format_type: str) -> List[ValidationResult]:
        """Validate dialogue structure"""
        results = []
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Check for empty lines or malformed entries
        malformed_lines = []
        for i, line in enumerate(lines):
            if format_type == "qa_pairs":
                if not re.match(r'^[QA]:\s*.+', line, re.IGNORECASE):
                    malformed_lines.append(i + 1)
            elif format_type in ["dialogue", "conversation"]:
                if not re.match(r'^\w+.*:\s*.+', line):
                    malformed_lines.append(i + 1)
        
        if malformed_lines:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                f"Malformed lines detected at: {', '.join(map(str, malformed_lines[:5]))}{'...' if len(malformed_lines) > 5 else ''}",
                "structure",
                "Ensure all lines follow the expected format pattern"
            ))
        
        # Check for balanced exchanges
        if format_type == "qa_pairs":
            q_count = len(re.findall(r'^Q:', text, re.MULTILINE | re.IGNORECASE))
            a_count = len(re.findall(r'^A:', text, re.MULTILINE | re.IGNORECASE))
            
            if q_count != a_count:
                results.append(ValidationResult(
                    ValidationLevel.CRITICAL,
                    f"Unbalanced Q&A pairs: {q_count} questions, {a_count} answers",
                    "structure",
                    "Ensure each question has a corresponding answer"
                ))
        
        return results
    
    def _validate_coherence(self, text: str) -> List[ValidationResult]:
        """Validate dialogue coherence and flow"""
        results = []
        
        # Simple coherence checks
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                "Very few sentences detected - may lack depth",
                "coherence",
                "Add more detailed content for better dialogue flow"
            ))
        
        # Check for question-answer flow in Q&A format
        if 'Q:' in text and 'A:' in text:
            qa_pairs = re.findall(r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)', text, re.DOTALL)
            
            for i, (question, answer) in enumerate(qa_pairs):
                # Check if question actually contains question indicators
                if not re.search(self.format_patterns['question_indicators'], question, re.IGNORECASE):
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        f"Question {i+1} may not be a proper question",
                        "coherence",
                        "Ensure questions contain question words or question marks"
                    ))
                
                # Check if answer is substantial
                if len(answer.split()) < 5:
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        f"Answer {i+1} appears too brief",
                        "coherence",
                        "Provide more detailed answers"
                    ))
        
        return results
    
    def _calculate_quality_score(self, text: str, validation_results: List[ValidationResult]) -> float:
        """Calculate overall quality score"""
        base_score = 1.0
        
        # Deduct points for validation issues
        for result in validation_results:
            if result.level == ValidationLevel.CRITICAL:
                base_score -= 0.3
            elif result.level == ValidationLevel.WARNING:
                base_score -= 0.1
            elif result.level == ValidationLevel.INFO:
                base_score -= 0.05
        
        # Bonus points for good characteristics
        words = text.split()
        word_count = len(words)
        
        # Length bonus
        if 50 <= word_count <= 500:
            base_score += 0.1
        
        # Variety bonus
        unique_words = set(word.lower() for word in words if len(word) > 3)
        if len(unique_words) / max(word_count, 1) > 0.6:
            base_score += 0.1
        
        # Format consistency bonus
        if re.search(r'(Q:|A:|Speaker|Person|Teacher|Student):', text):
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def _attempt_correction(self, text: str, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Attempt to automatically correct common issues"""
        corrected_text = text
        corrections_applied = []
        
        # Fix common formatting issues
        for result in validation_results:
            if result.level == ValidationLevel.CRITICAL and "format" in result.field:
                # Try to fix Q&A format
                if "Q&A" in result.message:
                    # Convert simple dialogue to Q&A format
                    lines = corrected_text.split('\n')
                    corrected_lines = []
                    
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line:
                            if i % 2 == 0:  # Even lines become questions
                                if not line.startswith('Q:'):
                                    line = f"Q: {line}"
                                    if not line.endswith('?'):
                                        line += "?"
                            else:  # Odd lines become answers
                                if not line.startswith('A:'):
                                    line = f"A: {line}"
                            corrected_lines.append(line)
                    
                    corrected_text = '\n'.join(corrected_lines)
                    corrections_applied.append("Converted to Q&A format")
        
        return {
            "corrected_text": corrected_text,
            "corrections_applied": corrections_applied,
            "original_text": text
        }
    
    def render_validation_interface(self, dialogue_text: str) -> DialogueValidationReport:
        """
        Render validation interface in Streamlit
        
        Args:
            dialogue_text: Text to validate
            
        Returns:
            DialogueValidationReport
        """
        st.subheader("✅ Dialogue Validation")
        
        # Validation options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            expected_format = st.selectbox(
                "Expected Format",
                options=["auto", "qa_pairs", "dialogue", "conversation"],
                index=0,
                help="Choose the expected dialogue format"
            )
        
        with col2:
            quality_threshold = st.slider(
                "Quality Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Minimum quality score to pass validation"
            )
        
        with col3:
            auto_correct = st.checkbox(
                "Auto-correct",
                value=True,
                help="Attempt automatic correction of issues"
            )
        
        # Update quality threshold
        self.quality_thresholds['min_quality_score'] = quality_threshold
        
        # Perform validation
        if dialogue_text:
            with st.spinner("Validating dialogue..."):
                report = self.validate_dialogue(dialogue_text, expected_format)
            
            # Display validation results
            self._display_validation_report(report, auto_correct)
            
            return report
        else:
            st.info("Enter dialogue text to validate")
            return DialogueValidationReport(
                is_valid=False,
                quality_score=0.0,
                validation_results=[],
                processing_time=0.0
            )
    
    def _display_validation_report(self, report: DialogueValidationReport, show_corrections: bool = True):
        """Display validation report in Streamlit"""
        
        # Overall status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if report.is_valid:
                st.success("✅ Valid")
            else:
                st.error("❌ Invalid")
        
        with col2:
            st.metric("Quality Score", f"{report.quality_score:.1%}")
        
        with col3:
            st.metric("Issues Found", len(report.validation_results))
        
        with col4:
            st.metric("Processing Time", f"{report.processing_time:.2f}s")
        
        # Detailed results
        if report.validation_results:
            st.subheader("🔍 Validation Details")
            
            # Group by severity
            critical_issues = [r for r in report.validation_results if r.level == ValidationLevel.CRITICAL]
            warnings = [r for r in report.validation_results if r.level == ValidationLevel.WARNING]
            info_items = [r for r in report.validation_results if r.level == ValidationLevel.INFO]
            
            # Display critical issues
            if critical_issues:
                st.error("🔴 Critical Issues")
                for issue in critical_issues:
                    st.write(f"• **{issue.field.title()}:** {issue.message}")
                    if issue.suggestion:
                        st.write(f"  💡 *Suggestion: {issue.suggestion}*")
            
            # Display warnings
            if warnings:
                st.warning("⚠️ Warnings")
                for warning in warnings:
                    st.write(f"• **{warning.field.title()}:** {warning.message}")
                    if warning.suggestion:
                        st.write(f"  💡 *Suggestion: {warning.suggestion}*")
            
            # Display info items
            if info_items:
                st.info("ℹ️ Information")
                for info in info_items:
                    st.write(f"• **{info.field.title()}:** {info.message}")
                    if info.suggestion:
                        st.write(f"  💡 *Suggestion: {info.suggestion}*")
        
        # Show corrections if available
        if show_corrections and report.corrected_dialogue and not report.is_valid:
            st.subheader("🔧 Suggested Corrections")
            
            corrected_text = report.corrected_dialogue.get("corrected_text", "")
            corrections_applied = report.corrected_dialogue.get("corrections_applied", [])
            
            if corrections_applied:
                st.write("**Applied Corrections:**")
                for correction in corrections_applied:
                    st.write(f"• {correction}")
            
            if corrected_text:
                st.text_area(
                    "Corrected Dialogue",
                    value=corrected_text,
                    height=200,
                    help="Automatically corrected version of the dialogue"
                )
                
                if st.button("📋 Use Corrected Version"):
                    st.session_state.corrected_dialogue = corrected_text
                    st.success("Corrected version saved to session!")
    
    def batch_validate(self, dialogues: List[str], format_type: str = "auto") -> List[DialogueValidationReport]:
        """
        Validate multiple dialogues in batch
        
        Args:
            dialogues: List of dialogue texts to validate
            format_type: Expected format for all dialogues
            
        Returns:
            List of validation reports
        """
        reports = []
        
        for i, dialogue in enumerate(dialogues):
            try:
                report = self.validate_dialogue(dialogue, format_type)
                reports.append(report)
            except Exception as e:
                # Create error report
                error_report = DialogueValidationReport(
                    is_valid=False,
                    quality_score=0.0,
                    validation_results=[ValidationResult(
                        ValidationLevel.CRITICAL,
                        f"Validation error: {str(e)}",
                        "system",
                        "Check dialogue format and content"
                    )],
                    processing_time=0.0
                )
                reports.append(error_report)
        
        return reports
    
    def export_validation_report(self, report: DialogueValidationReport) -> Dict[str, Any]:
        """Export validation report as dictionary"""
        return {
            "is_valid": report.is_valid,
            "quality_score": report.quality_score,
            "processing_time": report.processing_time,
            "validation_results": [
                {
                    "level": result.level.value,
                    "message": result.message,
                    "field": result.field,
                    "suggestion": result.suggestion
                }
                for result in report.validation_results
            ],
            "corrected_dialogue": report.corrected_dialogue,
            "timestamp": time.time()
        }

# Global instance
llm_output_validator = LLMOutputValidator()

def validate_dialogue_output(dialogue_text: str, expected_format: str = "auto") -> DialogueValidationReport:
    """
    Convenience function to validate dialogue output
    
    Args:
        dialogue_text: Text to validate
        expected_format: Expected format
        
    Returns:
        DialogueValidationReport
    """
    return llm_output_validator.validate_dialogue(dialogue_text, expected_format)

def render_validation_interface(dialogue_text: str) -> DialogueValidationReport:
    """
    Convenience function to render validation interface
    
    Args:
        dialogue_text: Text to validate
        
    Returns:
        DialogueValidationReport
    """
    return llm_output_validator.render_validation_interface(dialogue_text)

