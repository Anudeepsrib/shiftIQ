"""
Integration tests for complete migration workflows.

Tests end-to-end migration scenarios with all security,
compliance, and rollback features.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from code_migration.core.security import SecurityAuditLogger
from code_migration.core.confidence import MigrationConfidenceAnalyzer
from code_migration.core.visualizer import VisualMigrationPlanner
from code_migration.core.rollback import TimeMachineRollback
from code_migration.core.compliance import PIIDetector, AuditReporter


@pytest.mark.slow
@pytest.mark.integration
class TestFullMigrationWorkflow:
    """Test complete migration workflow integration."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary React project for testing."""
        # Create temp dir within project structure to satisfy PathSanitizer
        base_temp_dir = Path(__file__).parent.parent / "temp"
        base_temp_dir.mkdir(exist_ok=True)
        
        with tempfile.TemporaryDirectory(dir=base_temp_dir) as temp_dir:
            project_path = Path(temp_dir) / "react-project"
            project_path.mkdir()
            
            # Create React project structure
            (project_path / "src").mkdir()
            (project_path / "src" / "components").mkdir()
            (project_path / "src" / "utils").mkdir()
            
            # Create sample React class components
            (project_path / "src" / "components" / "UserProfile.jsx").write_text("""
import React, { Component } from 'react';
import axios from 'axios';

class UserProfile extends Component {
    constructor(props) {
        super(props);
        this.state = {
            user: null,
            loading: true,
            error: null
        };
        this.componentDidMount = this.componentDidMount.bind(this);
        self.fetchUser = this.fetchUser.bind(this);
        this.handleClick = this.handleClick.bind(this);
    }
    
    componentDidMount() {
        this.fetchUser();
    }
    
    componentWillUnmount() {
        // Cleanup
        if (this.timer) {
            clearTimeout(this.timer);
        }
    }
    
    componentDidUpdate(prevProps, prevState) {
        if (this.props.userId !== prevProps.userId) {
            this.fetchUser();
        }
    }
    
    async fetchUser() {
        try {
            this.setState({ loading: true });
            const response = await axios.get(`/api/users/${this.props.userId}`);
            this.setState({ 
                user: response.data, 
                loading: false,
                error: null 
            });
        } catch (error) {
            this.setState({ 
                error: error.message, 
                loading: false 
            });
        }
    }
    
    handleClick() {
        this.setState(prevState => ({
            user: { ...prevState.user, updated: true }
        }));
    }
    
    render() {
        const { user, loading, error } = this.state;
        
        if (loading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;
        if (!user) return <div>No user data</div>;
        
        return (
            <div className="user-profile">
                <h1>{user.name}</h1>
                <p>Email: {user.email}</p>
                <button onClick={this.handleClick}>
                    Update User
                </button>
            </div>
        );
    }
}

export default UserProfile;
""")
            
            (project_path / "src" / "components" / "Button.jsx").write_text("""
import React, { Component } from 'react';

class Button extends Component {
    constructor(props) {
        super(props);
        this.state = { clicked: false };
        this.handleClick = this.handleClick.bind(this);
    }
    
    handleClick() {
        this.setState({ clicked: true });
        if (this.props.onClick) {
            this.props.onClick();
        }
    }
    
    render() {
        const { label, variant = 'primary' } = this.props;
        const { clicked } = this.state;
        
        return (
            <button 
                className={`btn btn-${variant} ${clicked ? 'clicked' : ''}`}
                onClick={this.handleClick}
            >
                {label}
            </button>
        );
    }
}

export default Button;
""")
            
            (project_path / "src" / "utils" / "api.js").write_text("""
// API utilities
class API {
    constructor() {
        this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:3001';
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.REACT_APP_API_KEY}`
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
}

export default API;
""")
            
            # Create package.json
            (project_path / "package.json").write_text(json.dumps({
                "name": "react-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^16.14.0",
                    "axios": "^0.24.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "react-scripts test"
                }
            }, indent=2))
            
            # Create .env file with secrets (for testing)
            (project_path / ".env").write_text("""
REACT_APP_API_URL=https://api.example.com
REACT_APP_API_KEY=sk-1234567890abcdef
REACT_APP_USER_EMAIL=admin@example.com
REACT_APP_SUPPORT_PHONE=555-123-4567
""")
            
            yield project_path
    
    def test_confidence_analysis_workflow(self, temp_project):
        """Test complete confidence analysis workflow."""
        # Initialize confidence analyzer
        with MigrationConfidenceAnalyzer(temp_project) as analyzer:
            # Analyze migration confidence
            confidence_score = analyzer.calculate_confidence("react-hooks", team_experience=70)
            
            # Verify confidence score structure
            assert confidence_score.overall_score >= 0
            assert confidence_score.overall_score <= 100
            assert confidence_score.risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            assert confidence_score.estimated_hours > 0
            assert confidence_score.estimated_cost > 0
            assert 'test_coverage' in confidence_score.factors
            assert 'complexity' in confidence_score.factors
            assert 'dependencies' in confidence_score.factors
            assert 'code_quality' in confidence_score.factors
            assert 'breaking_changes' in confidence_score.factors
            assert 'team_experience' in confidence_score.factors
            
            # Verify recommendations are provided
            assert len(confidence_score.recommendations) > 0
            assert len(confidence_score.warnings) >= 0
            assert len(confidence_score.blockers) >= 0
            
            # Generate report
            report = analyzer.generate_report(confidence_score)
            assert "MIGRATION CONFIDENCE ANALYSIS" in report
            assert "Overall Confidence:" in report
            assert "RISK FACTORS:" in report
            assert "ESTIMATES:" in report
    
    def test_visual_planning_workflow(self, temp_project):
        """Test complete visual planning workflow."""
        # Initialize visual planner
        planner = VisualMigrationPlanner(temp_project)
        
        # Build dependency graph
        graph = planner.build_dependency_graph()
        
        # Verify graph structure
        assert graph.number_of_nodes() > 0
        assert graph.number_of_edges() >= 0
        
        # Calculate migration waves
        waves = planner.calculate_migration_waves()
        assert len(waves) > 0
        assert all(isinstance(wave, list) for wave in waves)
        
        # Get graph statistics
        stats = planner.get_graph_statistics()
        assert 'total_nodes' in stats
        assert 'total_edges' in stats
        assert 'file_nodes' in stats
        assert 'circular_dependencies' in stats
        
        # Generate visualization
        output_path = temp_project / "migration-graph.html"
        planner.generate_d3_visualization(output_path)
        assert output_path.exists()
        
        # Verify HTML content
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        assert "Migration Dependency Graph" in html_content
        assert "D3.js" in html_content
        assert "Migration Plan" in html_content
        
        # Export graph data
        json_path = temp_project / "graph-data.json"
        planner.export_graph_data(json_path)
        assert json_path.exists()
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            graph_data = json.load(f)
        assert 'metadata' in graph_data
        assert 'nodes' in graph_data
        assert 'links' in graph_data
        assert 'waves' in graph_data
    
    def test_rollback_workflow(self, temp_project):
        """Test complete rollback workflow."""
        # Initialize rollback system
        with TimeMachineRollback(temp_project) as rollback:
            # Create initial checkpoint
            checkpoint_id = rollback.create_checkpoint("Initial state")
            assert checkpoint_id is not None
            assert len(checkpoint_id) > 0
            
            # Verify checkpoint was created
            checkpoints = rollback.list_checkpoints()
            assert len(checkpoints) >= 1
            assert checkpoint_id in [cp['id'] for cp in checkpoints]
            
            # Get checkpoint details
            details = rollback.get_checkpoint_details(checkpoint_id)
            assert details is not None
            assert details['id'] == checkpoint_id
            assert details['description'] == "Initial state"
            assert 'timestamp' in details
            assert 'file_count' in details
            
            # Modify a file
            test_file = temp_project / "src" / "components" / "UserProfile.jsx"
            original_content = test_file.read_text(encoding='utf-8')
            test_file.write_text(original_content + "\n// Modified for testing\n", encoding='utf-8')
            
            # Verify file was modified
            assert test_file.read_text(encoding='utf-8') != original_content
            
            # Perform rollback
            rollback_result = rollback.rollback(checkpoint_id)
            assert rollback_result['success'] is True
            assert rollback_result['files_restored'] > 0
            
            # Verify file was restored
            assert test_file.read_text(encoding='utf-8') == original_content
            
            # Test partial rollback
            test_file.write_text(original_content + "\n// Modified again\n", encoding='utf-8')
            partial_result = rollback.rollback(
                checkpoint_id, 
                files=["src/components/UserProfile.jsx"]
            )
            assert partial_result['success'] is True
            assert test_file.read_text(encoding='utf-8') == original_content
            
            # Test rollback preview
            preview = rollback.rollback(checkpoint_id, dry_run=True)
            assert preview['dry_run'] is True
            assert 'files_restored' in preview
            assert 'changes' in preview
    
    def test_compliance_scanning_workflow(self, temp_project):
        """Test complete compliance scanning workflow."""
        # Initialize PII detector
        with PIIDetector(temp_project) as pii_detector:
            # Scan for PII
            scan_results = pii_detector.scan_directory()
            
            # Verify scan results structure
            assert 'scan_timestamp' in scan_results
            assert 'files_scanned' in scan_results
            assert 'files_with_pii' in scan_results
            assert 'total_findings' in scan_results
            assert 'summary' in scan_results
            assert 'findings' in scan_results
            
            # Should find PII in .env file
            assert scan_results['files_with_pii'] >= 1
            assert scan_results['total_findings'] >= 2  # email, phone check
            
            # Verify findings structure
            for finding in scan_results['findings']:
                assert 'type' in finding
                assert 'severity' in finding
                assert 'regulation' in finding
                assert 'file_path' in finding
                assert 'line' in finding
                assert 'recommendation' in finding
            
            # Generate compliance report
            report = pii_detector.generate_compliance_report(scan_results)
            assert "PII/PHI/PCI PATTERN SCAN REPORT" in report
            assert "GDPR" in report
            assert "CRITICAL FINDINGS" in report
            assert "RECOMMENDATIONS" in report
        
        # Initialize audit reporter
        with AuditReporter(temp_project) as audit_reporter:
            # Generate SOC2 report
            soc2_report = audit_reporter.generate_soc2_report()
            assert soc2_report['report_type'] == 'SOC2'
            assert 'trust_services_criteria' in soc2_report
            assert 'compliance_score' in soc2_report
            
            # Generate GDPR report
            gdpr_report = audit_reporter.generate_gdpr_report()
            assert gdpr_report['report_type'] == 'GDPR'
            assert 'gdpr_articles' in gdpr_report
            assert 'pii_processing' in gdpr_report
            
            # Export reports
            soc2_json_path = temp_project / "soc2-report.json"
            success = audit_reporter.export_report(soc2_report, soc2_json_path, 'json')
            assert success is True
            assert soc2_json_path.exists()
            
            gdpr_html_path = temp_project / "gdpr-report.html"
            success = audit_reporter.export_report(gdpr_report, gdpr_html_path, 'html')
            assert success is True
            assert gdpr_html_path.exists()
    
    def test_audit_logging_workflow(self, temp_project):
        """Test audit logging workflow."""
        # Initialize audit logger
        log_dir = temp_project / '.migration-logs'
        with SecurityAuditLogger(log_dir) as audit_logger:
            # Log various events
            audit_logger.log_migration_event(
                migration_type="react-hooks",
                project_path=str(temp_project),
                user="test-user",
                action="ANALYSIS_START",
                result="SUCCESS"
            )
            
            audit_logger.log_file_access(
                file_path="src/components/UserProfile.jsx",
                user="test-user",
                action="READ",
                result="SUCCESS",
                file_size=1024
            )
            
            audit_logger.log_security_violation(
                violation_type="POTENTIAL_INJECTION",
                user="test-user",
                resource="src/components/UserProfile.jsx",
                details={"pattern": "eval"}
            )
            
            # Verify audit log was created
            audit_log = log_dir / "security_audit.jsonl"
            assert audit_log.exists()
            
            # Search logs
            events = audit_logger.search_logs(limit=10)
            assert len(events) >= 3
            
            # Verify event structure
            for event in events:
                assert 'event_id' in event
                assert 'timestamp_utc' in event
                assert 'user' in event
                assert 'action' in event
                assert 'result' in event
                assert 'compliance' in event
            
            # Generate compliance report
            compliance_report = audit_logger.generate_compliance_report()
            assert 'report_period' in compliance_report
            assert 'summary' in compliance_report
            assert 'top_users' in compliance_report
            assert 'security_events' in compliance_report
    
    def test_end_to_end_migration_simulation(self, temp_project):
        """Test complete end-to-end migration simulation."""
        # Step 1: Confidence Analysis
        with MigrationConfidenceAnalyzer(temp_project) as analyzer:
            confidence = analyzer.calculate_confidence("react-hooks")
        
        # Step 2: Visual Planning
        planner = VisualMigrationPlanner(temp_project)
        planner.build_dependency_graph()
        waves = planner.calculate_migration_waves()
        
        # Step 3: Create Checkpoint
        with TimeMachineRollback(temp_project) as rollback:
            checkpoint_id = rollback.create_checkpoint("Pre-migration backup")
            
            # Step 4: Compliance Scan
            with PIIDetector(temp_project) as pii_detector:
                compliance_results = pii_detector.scan_directory()
            
            # Step 5: Generate Reports
            with AuditReporter(temp_project) as audit_reporter:
                soc2_report = audit_reporter.generate_soc2_report()
            
            # Step 6: Simulate Migration (modify files)
            for wave_files in waves[:2]:  # Simulate first 2 waves
                for wave_files_list in [wave_files]: # handle potential nested list structure if wave_files is a list of files
                    if isinstance(wave_files, str): # if wave_files is string (filename), wrap in list
                         wave_files_list = [wave_files]
                    elif isinstance(wave_files, list):
                         wave_files_list = wave_files
                         
                    for file_path in wave_files_list:
                        full_path = temp_project / file_path
                        if full_path.exists():
                            content = full_path.read_text(encoding='utf-8')
                            # Simulate migration by adding comment
                            full_path.write_text(content + "\n// Migrated to hooks\n", encoding='utf-8')
            
            # Step 7: Verify Results
            assert confidence.overall_score > 0
            assert len(waves) > 0
            assert checkpoint_id is not None
            assert compliance_results['total_findings'] >= 0
            assert soc2_report['report_type'] == 'SOC2'
            
            # Step 8: Cleanup (rollback)
            rollback.rollback(checkpoint_id)
            
            # Verify rollback worked
            test_file = temp_project / "src" / "components" / "UserProfile.jsx"
            assert "// Migrated to hooks" not in test_file.read_text(encoding='utf-8')


class TestMigrationErrorHandling:
    """Test error handling and edge cases in migration workflows."""
    
    @pytest.fixture
    def empty_project(self):
        """Create an empty project for error testing."""
        # Create temp dir within project structure to satisfy PathSanitizer
        base_temp_dir = Path(__file__).parent.parent / "temp"
        base_temp_dir.mkdir(exist_ok=True)
        
        with tempfile.TemporaryDirectory(dir=base_temp_dir) as temp_dir:
            project_path = Path(temp_dir) / "empty-project"
            project_path.mkdir()
            yield project_path

    @pytest.fixture
    def error_temp_project(self):
        """Create a temporary React project for testing error handling."""
        # Create temp dir within project structure to satisfy PathSanitizer
        base_temp_dir = Path(__file__).parent.parent / "temp"
        base_temp_dir.mkdir(exist_ok=True)
        
        with tempfile.TemporaryDirectory(dir=base_temp_dir) as temp_dir:
            project_path = Path(temp_dir) / "react-project"
            project_path.mkdir()
            
            # Create React project structure
            (project_path / "src").mkdir()
            (project_path / "src" / "components").mkdir()
            (project_path / "src" / "utils").mkdir()
            
            # Create sample React class components
            (project_path / "src" / "components" / "UserProfile.jsx").write_text("""
import React, { Component } from 'react';
import axios from 'axios';

class UserProfile extends Component {
    constructor(props) {
        super(props);
        this.state = {
            user: null,
            loading: true,
            error: null
        };
    }
    render() {
        return <div>Test</div>;
    }
}
export default UserProfile;
""")
            # Create .env file with secrets (for testing)
            (project_path / ".env").write_text("""
REACT_APP_API_URL=https://api.example.com
REACT_APP_API_KEY=sk-1234567890abcdef
""")
            yield project_path
    
    def test_empty_project_handling(self, empty_project):
        """Test handling of empty projects."""
        # Confidence analysis on empty project
        with MigrationConfidenceAnalyzer(empty_project) as analyzer:
            confidence = analyzer.calculate_confidence("react-hooks")
            
            # Should still return valid structure with low scores
            assert confidence.overall_score >= 0
            assert confidence.risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        # Visual planning on empty project
        planner = VisualMigrationPlanner(empty_project)
        graph = planner.build_dependency_graph()
        
        # Should handle empty project gracefully
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0
        
        waves = planner.calculate_migration_waves()
        assert len(waves) == 0
        
        # Rollback on empty project
        with TimeMachineRollback(empty_project) as rollback:
            checkpoint_id = rollback.create_checkpoint("Empty project checkpoint")
            
            assert checkpoint_id is not None
            assert rollback.list_checkpoints()[0]['file_count'] == 0
    
    def test_invalid_migration_type(self, error_temp_project):
        """Test handling of invalid migration types."""
        with MigrationConfidenceAnalyzer(error_temp_project) as analyzer:
            # Should handle invalid migration type gracefully
            with pytest.raises(Exception):  # Should raise validation error
                analyzer.calculate_confidence("invalid-type")
    
    def test_corrupted_file_handling(self, error_temp_project):
        """Test handling of corrupted or unreadable files."""
        # Create corrupted file
        corrupted_file = error_temp_project / "corrupted.py"
        corrupted_file.write_bytes(b'\\x00\\x01\\x02\\x03\\x04\\x05')
        
        # Should handle corrupted file gracefully
        with MigrationConfidenceAnalyzer(error_temp_project) as analyzer:
            confidence = analyzer.calculate_confidence("react-hooks")
            
            # Should still return valid structure
            assert confidence.overall_score >= 0
    
    def test_permission_denied_handling(self, error_temp_project):
        """Test handling of permission issues."""
        # Create file and remove read permissions (if possible)
        test_file = error_temp_project / "restricted.py"
        test_file.write_text("print('test')")
        
        try:
            # Try to remove read permissions
            test_file.chmod(0o000)
            
            # Should handle permission issues gracefully
            with MigrationConfidenceAnalyzer(error_temp_project) as analyzer:
                confidence = analyzer.calculate_confidence("react-hooks")
                
                # Should still return valid structure
                assert confidence.overall_score >= 0
            
        except OSError:
            # Permission changes not supported on this system
            pass
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except OSError:
                pass
    
    def test_rollback_to_nonexistent_checkpoint(self, error_temp_project):
        """Test rollback to non-existent checkpoint."""
        with TimeMachineRollback(error_temp_project) as rollback:
            # Should raise error for non-existent checkpoint
            with pytest.raises(ValueError):
                rollback.rollback("non-existent-checkpoint")
    
    def test_compliance_scan_with_malformed_files(self, error_temp_project):
        """Test compliance scanning with malformed files."""
        # Create malformed JSON file
        malformed_json = error_temp_project / "malformed.json"
        malformed_json.write_text('{"invalid": json content}', encoding='utf-8')
        
        # Create file with binary content
        binary_file = error_temp_project / "binary.dat"
        binary_file.write_bytes(b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR')
        
        # Should handle malformed files gracefully
        with PIIDetector(error_temp_project) as detector:
            results = detector.scan_directory()
            
            # Should still return valid structure
            assert 'files_scanned' in results
            assert 'total_findings' in results
            assert isinstance(results['total_findings'], int)
