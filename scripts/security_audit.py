#!/usr/bin/env python3
"""
Security Audit Script
====================

Automated security audit for the CRS3 CodeAnalytics Dashboard.
Checks for common vulnerabilities and security issues.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.security_config import SecurityConfig

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Performs security audits on the codebase"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = []
        self.stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
    
    def add_issue(self, severity: str, category: str, file_path: str, 
                  line_num: int, description: str, recommendation: str = ""):
        """Add a security issue to the report"""
        issue = {
            'severity': severity,
            'category': category,
            'file': str(file_path),
            'line': line_num,
            'description': description,
            'recommendation': recommendation
        }
        self.issues.append(issue)
        self.stats['issues_found'] += 1
        self.stats[severity.lower()] += 1
    
    def scan_file_for_patterns(self, file_path: Path, patterns: List[Tuple[str, str, str]]):
        """Scan a file for security patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, severity, description in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.add_issue(
                            severity=severity,
                            category="Pattern Match",
                            file_path=file_path,
                            line_num=line_num,
                            description=description,
                            recommendation="Review and fix the identified security issue"
                        )
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets and API keys"""
        logger.info("Checking for hardcoded secrets...")
        
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Potential hardcoded API key'),
            (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Potential hardcoded secret key'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Potential hardcoded password'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Potential hardcoded token'),
            (r'aws[_-]?access[_-]?key', 'HIGH', 'Potential AWS credentials'),
            (r'private[_-]?key', 'HIGH', 'Potential private key'),
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            self.stats['files_scanned'] += 1
            self.scan_file_for_patterns(py_file, secret_patterns)
    
    def check_sql_injection(self):
        """Check for potential SQL injection vulnerabilities"""
        logger.info("Checking for SQL injection vulnerabilities...")
        
        sql_patterns = [
            (r'execute\s*\(\s*["\'].*%s', 'MEDIUM', 'String formatting in SQL query'),
            (r'execute\s*\(\s*f["\']', 'HIGH', 'F-string in SQL query'),
            (r'execute\s*\(\s*[^,]+\+', 'HIGH', 'String concatenation in SQL query'),
            (r'cursor\.execute\([^,)]+format\(', 'HIGH', 'Format string in SQL query'),
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            self.scan_file_for_patterns(py_file, sql_patterns)
    
    def check_xss_vulnerabilities(self):
        """Check for potential XSS vulnerabilities"""
        logger.info("Checking for XSS vulnerabilities...")
        
        xss_patterns = [
            (r'unsafe_allow_html\s*=\s*True', 'MEDIUM', 'Unsafe HTML rendering enabled'),
            (r'st\.markdown\([^)]+unsafe_allow_html\s*=\s*True', 'MEDIUM', 'Unsafe markdown rendering'),
            (r'innerHTML\s*=', 'HIGH', 'Direct innerHTML assignment'),
            (r'document\.write\(', 'HIGH', 'document.write usage'),
        ]
        
        for file_path in self.root_path.rglob("*.py"):
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
            self.scan_file_for_patterns(file_path, xss_patterns)
    
    def check_path_traversal(self):
        """Check for path traversal vulnerabilities"""
        logger.info("Checking for path traversal vulnerabilities...")
        
        path_patterns = [
            (r'open\s*\([^)]*\+', 'MEDIUM', 'String concatenation in file path'),
            (r'Path\s*\([^)]*\+', 'MEDIUM', 'String concatenation in Path constructor'),
            (r'os\.path\.join\s*\([^)]*request', 'HIGH', 'User input in file path'),
            (r'open\s*\([^)]*request', 'HIGH', 'User input in file open'),
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            self.scan_file_for_patterns(py_file, path_patterns)
    
    def check_dependencies(self):
        """Check dependencies for known vulnerabilities"""
        logger.info("Checking dependencies for vulnerabilities...")
        
        try:
            # Run safety check if available
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and result.stdout:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    self.add_issue(
                        severity='HIGH',
                        category='Dependency',
                        file_path='requirements.txt',
                        line_num=0,
                        description=f"Vulnerable dependency: {vuln['package']} {vuln['installed_version']}",
                        recommendation=f"Update to {vuln['recommendation']}"
                    )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Safety tool not available. Install with: pip install safety")
    
    def check_error_handling(self):
        """Check for proper error handling"""
        logger.info("Checking error handling...")
        
        error_patterns = [
            (r'except\s*:', 'LOW', 'Bare except clause'),
            (r'except\s+Exception\s*:', 'LOW', 'Catching generic Exception'),
            (r'pass\s*$', 'MEDIUM', 'Empty except block with pass'),
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            self.scan_file_for_patterns(py_file, error_patterns)
    
    def run_bandit_scan(self):
        """Run bandit security scanner if available"""
        logger.info("Running bandit security scan...")
        
        try:
            result = subprocess.run(
                ['bandit', '-r', str(self.root_path), '-f', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                for issue in bandit_results.get('results', []):
                    self.add_issue(
                        severity=issue['issue_severity'],
                        category='Bandit',
                        file_path=issue['filename'],
                        line_num=issue['line_number'],
                        description=issue['issue_text'],
                        recommendation=issue.get('more_info', '')
                    )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Bandit tool not available. Install with: pip install bandit")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate security audit report"""
        report = {
            'summary': self.stats,
            'issues': sorted(self.issues, key=lambda x: (
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x['severity'], 4),
                x['file'],
                x['line']
            ))
        }
        return report
    
    def run_full_audit(self):
        """Run complete security audit"""
        logger.info("Starting security audit...")
        
        self.check_hardcoded_secrets()
        self.check_sql_injection()
        self.check_xss_vulnerabilities()
        self.check_path_traversal()
        self.check_error_handling()
        self.check_dependencies()
        self.run_bandit_scan()
        
        logger.info(f"Audit complete. Found {self.stats['issues_found']} issues.")

def main():
    parser = argparse.ArgumentParser(description='Security audit for CRS3 CodeAnalytics Dashboard')
    parser.add_argument('--path', default='.', help='Path to scan (default: current directory)')
    parser.add_argument('--output', help='Output file for JSON report')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor(args.path)
    auditor.run_full_audit()
    
    report = auditor.generate_report()
    
    if args.format == 'json' or args.output:
        json_report = json.dumps(report, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_report)
            logger.info(f"Report saved to {args.output}")
        else:
            print(json_report)
    else:
        # Text format output
        print("\n" + "="*60)
        print("SECURITY AUDIT REPORT")
        print("="*60)
        print(f"\nSummary:")
        print(f"  Files scanned: {report['summary']['files_scanned']}")
        print(f"  Total issues: {report['summary']['issues_found']}")
        print(f"  Critical: {report['summary']['critical']}")
        print(f"  High: {report['summary']['high']}")
        print(f"  Medium: {report['summary']['medium']}")
        print(f"  Low: {report['summary']['low']}")
        
        if report['issues']:
            print("\n" + "-"*60)
            print("ISSUES FOUND:")
            print("-"*60)
            
            for issue in report['issues']:
                print(f"\n[{issue['severity']}] {issue['category']}")
                print(f"File: {issue['file']}:{issue['line']}")
                print(f"Description: {issue['description']}")
                if issue['recommendation']:
                    print(f"Recommendation: {issue['recommendation']}")

if __name__ == '__main__':
    main()