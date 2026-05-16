"""
Test suite for PII detection compliance scanning.

Tests PII/PHI/PCI pattern scanning behavior.
"""

import pytest
from pathlib import Path
from datetime import datetime

from code_migration.core.compliance import PIIDetector


class TestPIIDetector:
    """Test PII detection and compliance scanning."""

    @pytest.fixture
    def detector(self, temp_project_dir):
        """Create and clean up PII detector."""
        detector = PIIDetector(temp_project_dir)
        yield detector
        detector.close()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files."""
        from tempfile import TemporaryDirectory
        import json
        
        with TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test files with PII
            (project_path / "user_profile.py").write_text("""
# User profile with PII
class UserProfile:
    def __init__(self):
        self.email = "john.doe@example.com"
        self.phone = "555-123-4567"
        self.ssn = "123-45-6789"
        self.credit_card = "4242-4242-4242-4242"
        self.address = "123 Main Street, Anytown, USA 12345"
        self.dob = "01/15/1980"
        
    def save_to_database(self):
        # Database connection string
        conn = "postgresql://user:password@localhost/db"
        pass
""")
            
            (project_path / "medical_record.py").write_text("""
# Medical record with PHI
class MedicalRecord:
    def __init__(self):
        self.mrn = "MRN123456"
        self.patient_id = "PAT789012"
        self.diagnosis_code = "ICD10 J45.909"
        self.procedure_code = "CPT99213"
        self.insurance = "987-65-4321"
        
    def log_access(self):
        # Log PHI access
        print(f"Accessed patient {self.patient_id}")
""")
            
            (project_path / "config.json").write_text(json.dumps({
                "database_url": "mysql://user:secret@localhost/production",
                "api_key": "sk-1234567890abcdef",
                "webhook": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
            }, indent=2))
            
            (project_path / "safe_file.py").write_text("""
# Safe file without PII
class SafeClass:
    def __init__(self):
        self.name = "example_value"
        self.value = 42
        
    def calculate(self):
        return self.value * 2
""")
            
            yield project_path
    
    def test_email_detection(self, detector, temp_project_dir):
        """Test email address detection."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) >= 1
        
        email_finding = email_findings[0]
        assert email_finding['severity'] == 'MEDIUM'
        assert email_finding['confidence'] == 'HIGH'
        assert email_finding['regulation'] == 'GDPR'
        assert email_finding['match'].startswith('[REDACTED:')
        assert 'raw_match' not in email_finding
        assert 'fingerprint' in email_finding
    
    def test_phone_detection(self, detector, temp_project_dir):
        """Test phone number detection."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        phone_findings = [f for f in findings if f['type'] == 'phone']
        assert len(phone_findings) >= 1
        
        phone_finding = phone_findings[0]
        assert phone_finding['severity'] == 'MEDIUM'
        assert phone_finding['confidence'] == 'MEDIUM'
        assert phone_finding['regulation'] == 'GDPR'
        assert phone_finding['match'].startswith('[REDACTED:')
    
    def test_ssn_detection(self, detector, temp_project_dir):
        """Test Social Security Number detection."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        ssn_findings = [f for f in findings if f['type'] == 'ssn']
        assert len(ssn_findings) >= 1
        
        ssn_finding = ssn_findings[0]
        assert ssn_finding['severity'] == 'HIGH'
        assert ssn_finding['confidence'] == 'HIGH'
        assert ssn_finding['regulation'] == 'GDPR'
        assert ssn_finding['match'].startswith('[REDACTED:')
    
    def test_credit_card_detection(self, detector, temp_project_dir):
        """Test credit card number detection."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        cc_findings = [f for f in findings if f['type'] == 'credit_card']
        assert len(cc_findings) >= 1
        
        cc_finding = cc_findings[0]
        assert cc_finding['severity'] == 'CRITICAL'
        assert cc_finding['confidence'] == 'HIGH'
        assert cc_finding['regulation'] == 'PCI-DSS'
        assert cc_finding['match'].startswith('[REDACTED:')
    
    def test_phi_detection(self, detector, temp_project_dir):
        """Test Protected Health Information detection."""
        
        findings = detector.scan_file(temp_project_dir / "medical_record.py")
        
        phi_findings = [f for f in findings if f['regulation'] == 'HIPAA']
        assert len(phi_findings) >= 3  # MRN, patient_id, diagnosis_code
        
        # Check MRN detection
        mrn_findings = [f for f in phi_findings if f['type'] == 'medical_record']
        assert len(mrn_findings) >= 1
        assert mrn_findings[0]['severity'] == 'CRITICAL'
        assert mrn_findings[0]['match'].startswith('[REDACTED:')
        
        # Check patient ID detection
        patient_findings = [f for f in phi_findings if f['type'] == 'patient_id']
        assert len(patient_findings) >= 1
        assert patient_findings[0]['severity'] == 'CRITICAL'
        assert patient_findings[0]['match'].startswith('[REDACTED:')
    
    def test_directory_scan(self, detector):
        """Test directory-wide PII scanning."""
        
        results = detector.scan_directory()
        
        assert results['files_scanned'] >= 3  # Python files
        assert results['files_with_pii'] >= 2  # Files with PII
        assert results['total_findings'] >= 10  # Total PII findings
        
        # Check summary
        summary = results['summary']
        assert 'by_severity' in summary
        assert 'by_regulation' in summary
        assert 'risk_score' in summary
        
        # Should have critical findings
        assert summary['by_severity']['CRITICAL'] > 0
        
        # Should have GDPR and HIPAA findings
        assert 'GDPR' in summary['by_regulation']
        assert 'HIPAA' in summary['by_regulation']
    
    def test_safe_file_no_findings(self, detector, temp_project_dir):
        """Test that files without PII return no findings."""
        
        findings = detector.scan_file(temp_project_dir / "safe_file.py")
        
        assert len(findings) == 0
    
    def test_compliance_report_generation(self, detector):
        """Test compliance report generation."""
        
        results = detector.scan_directory()
        report = detector.generate_compliance_report(results)
        
        assert "PII/PHI/PCI PATTERN SCAN REPORT" in report
        assert "GDPR" in report
        assert "HIPAA" in report
        assert "PCI-DSS" in report
        assert "CRITICAL FINDINGS" in report
        assert "RECOMMENDATIONS" in report
        assert "4242-4242-4242-4242" not in report
    
    def test_context_generation(self, detector, temp_project_dir):
        """Test context generation for PII findings."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        for finding in findings:
            context = finding['context']
            assert '[REDACTED]' in context
            assert len(context) <= 200  # Should be truncated if too long
    
    def test_recommendation_generation(self, detector, temp_project_dir):
        """Test recommendation generation for different PII types."""
        
        findings = detector.scan_file(temp_project_dir / "user_profile.py")
        
        # Check that each finding has a recommendation
        for finding in findings:
            assert 'recommendation' in finding
            assert len(finding['recommendation']) > 0
        assert len(finding['recommendation']) > 0
    
    def test_file_extension_filtering(self, detector):
        """Test scanning specific file extensions."""
        
        # Scan only Python files
        results = detector.scan_directory(file_extensions=['.py'])
        
        assert results['files_scanned'] >= 3  # Python files
        assert results['total_findings'] >= 10  # PII in Python files
        
        # Scan only JSON files
        json_results = detector.scan_directory(file_extensions=['.json'])
        
        assert json_results['files_scanned'] >= 1  # JSON file
        assert json_results['total_findings'] >= 1  # API key-like value


class TestPIIDetectorEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def detector(self, temp_project_dir):
        """Create and clean up PII detector."""
        detector = PIIDetector(temp_project_dir)
        yield detector
        detector.close()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for edge case testing."""
        from tempfile import TemporaryDirectory
        
        with TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create edge case files
            (project_path / "edge_cases.py").write_text("""
# Edge case PII patterns
class EdgeCases:
    def __init__(self):
        # Malformed email
        self.bad_email = "user@.com"
        
        # Partial SSN
        self.partial_ssn = "123-45"
        
        # Phone with extensions
        self.phone_ext = "555-123-4567 x123"
        
        # International phone
        self.intl_phone = "+1-555-123-4567"
        
        # Credit card with spaces
        self.cc_spaces = "4242 4242 4242 4242"
        
        # IP address
        self.ip_address = "192.168.1.1"
        
        # Date patterns
        self.dob_slashes = "01/15/1980"
        self.dob_dashes = "1980-01-15"
""")
            
            yield project_path
    
    def test_malformed_pii_patterns(self, detector, temp_project_dir):
        """Test handling of malformed PII patterns."""
        
        findings = detector.scan_file(temp_project_dir / "edge_cases.py")
        
        # Should still detect some patterns despite being malformed
        assert len(findings) >= 3  # IP address, dates, partial patterns
    
    def test_international_phone_detection(self, detector, temp_project_dir):
        """Test international phone number detection."""
        
        findings = detector.scan_file(temp_project_dir / "edge_cases.py")
        
        phone_findings = [f for f in findings if f['type'] == 'phone']
        assert len(phone_findings) >= 1
        
        # Should detect both US and international formats
        phone_matches = [f['match'] for f in phone_findings]
        assert all(match.startswith('[REDACTED:') for match in phone_matches)
    
    def test_ip_address_detection(self, detector, temp_project_dir):
        """Test IP address detection."""
        
        findings = detector.scan_file(temp_project_dir / "edge_cases.py")
        
        ip_findings = [f for f in findings if f['type'] == 'ip_address']
        assert len(ip_findings) >= 1
        
        ip_finding = ip_findings[0]
        assert ip_finding['severity'] == 'LOW'
        assert ip_finding['match'].startswith('[REDACTED:')
    
    def test_date_pattern_detection(self, detector, temp_project_dir):
        """Test various date pattern detection."""
        
        findings = detector.scan_file(temp_project_dir / "edge_cases.py")
        
        date_findings = [f for f in findings if f['type'] == 'date_of_birth']
        assert len(date_findings) >= 1
        
        # Should detect both slash and dash formats
        date_matches = [f['match'] for f in date_findings]
        assert all(match.startswith('[REDACTED:') for match in date_matches)
    
    def test_empty_file_handling(self, temp_project_dir):
        """Test handling of empty files."""
        empty_file = temp_project_dir / "empty.py"
        empty_file.write_text("")
        
        with PIIDetector(temp_project_dir) as detector:
            findings = detector.scan_file(empty_file)
            assert len(findings) == 0
    
    def test_unicode_pii_handling(self, detector, temp_project_dir):
        """Test handling of Unicode characters in PII."""
        unicode_file = temp_project_dir / "unicode.py"
        unicode_file.write_text("""
# Unicode PII
class UnicodePII:
    def __init__(self):
        self.email = "用户@example.com"  # Unicode email
        self.name = "张三"  # Unicode name
""", encoding='utf-8')
        
        findings = detector.scan_file(unicode_file)
        
        # Should detect email pattern even with Unicode
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) >= 1
    
    def test_large_file_handling(self, detector, temp_project_dir):
        """Test handling of large files."""
        # Create a large file with some PII
        large_file = temp_project_dir / "large.py"
        
        # Generate content with PII scattered throughout
        content = "# Large file with PII\n"
        for i in range(1000):
            if i % 100 == 0:
                content += f'email = "user{i}@example.com"\n'
            else:
                content += f'x = {i}\n'
        
        large_file.write_text(content)
        
        findings = detector.scan_file(large_file)
        
        # Should detect the PII even in large files
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) >= 10  # Should find multiple emails
    
    def test_nested_pii_in_strings(self, detector, temp_project_dir):
        """Test PII detection in nested string contexts."""
        nested_file = temp_project_dir / "nested.py"
        nested_file.write_text("""
# Nested PII in strings
class NestedPII:
    def __init__(self):
        # PII in f-strings
        self.f_string_email = f"Contact: john.doe@example.com"
        
        # PII in concatenated strings
        self.concat_email = "john" + "." + "doe" + "@example.com"
        
        # PII in raw strings
        self.raw_email = r"john.doe@example.com"
        
        # PII in multiline strings
        self.multiline = '''
        Contact: jane.doe@example.com
        Phone: 555-987-6543
        '''
""")
        
        findings = detector.scan_file(nested_file)
        
        # Should detect PII in various string contexts
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) >= 3  # Multiple email formats
        
        phone_findings = [f for f in findings if f['type'] == 'phone']
        assert len(phone_findings) >= 1
