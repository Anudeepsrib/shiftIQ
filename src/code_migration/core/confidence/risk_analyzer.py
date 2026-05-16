"""
Risk analysis engine for migration assessment.

Identifies and categorizes migration risks:
- Technical risks
- Business risks
- Security risks
- Operational risks
"""

import re
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List

from ..security import SafeCodeAnalyzer


class RiskLevel(Enum):
    """Risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(Enum):
    """Risk categories."""
    TECHNICAL = "TECHNICAL"
    BUSINESS = "BUSINESS"
    SECURITY = "SECURITY"
    OPERATIONAL = "OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"


@dataclass
class Risk:
    """Individual risk assessment."""
    title: str
    description: str
    category: RiskCategory
    level: RiskLevel
    probability: int  # 0-100
    impact: int      # 0-100
    mitigation: str
    file_paths: List[str]


class RiskAnalyzer:
    """
    Analyzes migration risks using multiple heuristics.
    
    Categories:
    - Technical: Code complexity, dependencies, breaking changes
    - Business: Downtime, user impact, revenue impact
    - Security: Vulnerabilities, data exposure
    - Operational: Team capacity, tooling, environment
    - Compliance: Regulatory requirements
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize risk analyzer.
        
        Args:
            project_path: Path to project to analyze
        """
        self.project_path = Path(project_path)
        self.code_analyzer = SafeCodeAnalyzer()
        self.risks: List[Risk] = []
    
    def analyze_risks(self, migration_type: str) -> List[Risk]:
        """
        Perform comprehensive risk analysis.
        
        Args:
            migration_type: Type of migration to analyze
            
        Returns:
            List of identified risks
        """
        self.risks = []
        
        # Technical risks
        self._analyze_technical_risks(migration_type)
        
        # Security risks
        self._analyze_security_risks()
        
        # Operational risks
        self._analyze_operational_risks(migration_type)
        
        # Business risks
        self._analyze_business_risks(migration_type)
        
        # Compliance risks
        self._analyze_compliance_risks()
        
        # Sort by risk score (probability * impact)
        self.risks.sort(key=lambda r: r.probability * r.impact, reverse=True)
        
        return self.risks
    
    def _analyze_technical_risks(self, migration_type: str) -> None:
        """Analyze technical risks."""
        try:
            # Code complexity risk
            analysis = self.code_analyzer.analyze_directory(self.project_path)
            avg_complexity = analysis.get('avg_complexity', 0)
            
            if avg_complexity > 20:
                self.risks.append(Risk(
                    title="High Code Complexity",
                    description=f"Average cyclomatic complexity is {avg_complexity:.1f}, which is very high",
                    category=RiskCategory.TECHNICAL,
                    level=RiskLevel.HIGH,
                    probability=80,
                    impact=70,
                    mitigation="Refactor complex functions before migration. Break down large functions into smaller, testable units.",
                    file_paths=[]
                ))
            elif avg_complexity > 10:
                self.risks.append(Risk(
                    title="Moderate Code Complexity",
                    description=f"Average cyclomatic complexity is {avg_complexity:.1f}",
                    category=RiskCategory.TECHNICAL,
                    level=RiskLevel.MEDIUM,
                    probability=60,
                    impact=50,
                    mitigation="Consider refactoring the most complex functions before migration.",
                    file_paths=[]
                ))
            
            # Breaking changes risk
            breaking_patterns = self._get_breaking_change_patterns(migration_type)
            if breaking_patterns:
                high_risk_files = self._find_high_risk_files(breaking_patterns)
                
                if high_risk_files:
                    self.risks.append(Risk(
                        title="Breaking Changes Required",
                        description=f"Found {len(high_risk_files)} files requiring breaking changes",
                        category=RiskCategory.TECHNICAL,
                        level=RiskLevel.HIGH,
                        probability=90,
                        impact=80,
                        mitigation="Plan for incremental migration. Create compatibility layers where possible.",
                        file_paths=high_risk_files[:5]  # Top 5 files
                    ))
            
            # Dependency risks
            self._analyze_dependency_risks()
            
        except Exception:
            # Continue with other risk analyses if technical analysis fails
            pass
    
    def _analyze_security_risks(self) -> None:
        """Analyze security risks."""
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        files_with_secrets = []
        
        for pattern in secret_patterns:
            try:
                for file_path in self.project_path.rglob('*'):
                    if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue']:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if re.search(pattern, content, re.IGNORECASE):
                            files_with_secrets.append(str(file_path.relative_to(self.project_path)))
            except Exception:
                continue
        
        if files_with_secrets:
            self.risks.append(Risk(
                title="Hardcoded Secrets Detected",
                description=f"Found potential hardcoded secrets in {len(files_with_secrets)} files",
                category=RiskCategory.SECURITY,
                level=RiskLevel.CRITICAL,
                probability=95,
                impact=90,
                mitigation="Remove all hardcoded secrets and use environment variables or secret management systems.",
                file_paths=files_with_secrets[:5]
            ))
        
        # Check for unsafe imports
        unsafe_imports = ['eval', 'exec', 'compile', '__import__']
        files_with_unsafe_imports = []
        
        for file_path in self.project_path.rglob('*.py'):
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                for unsafe in unsafe_imports:
                    if unsafe in content:
                        files_with_unsafe_imports.append(str(file_path.relative_to(self.project_path)))
                        break
            except Exception:
                continue
        
        if files_with_unsafe_imports:
            self.risks.append(Risk(
                title="Unsafe Code Execution",
                description=f"Found potentially unsafe code execution in {len(files_with_unsafe_imports)} files",
                category=RiskCategory.SECURITY,
                level=RiskLevel.HIGH,
                probability=70,
                impact=85,
                mitigation="Review and remove unsafe code execution patterns. Use safer alternatives.",
                file_paths=files_with_unsafe_imports[:5]
            ))
    
    def _analyze_operational_risks(self, migration_type: str) -> None:
        """Analyze operational risks."""
        # Team experience risk
        self.risks.append(Risk(
            title="Team Learning Curve",
            description=f"Team may need training for {migration_type} migration",
            category=RiskCategory.OPERATIONAL,
            level=RiskLevel.MEDIUM,
            probability=70,
            impact=60,
            mitigation="Schedule training sessions. Start with a pilot migration. Consider hiring experienced consultants.",
            file_paths=[]
        ))
        
        # Tooling risk
        required_tools = self._get_required_tools(migration_type)
        missing_tools = []
        
        for tool in required_tools:
            if shutil.which(tool) is None:
                missing_tools.append(tool)
        
        if missing_tools:
            self.risks.append(Risk(
                title="Missing Required Tools",
                description=f"Missing tools: {', '.join(missing_tools)}",
                category=RiskCategory.OPERATIONAL,
                level=RiskLevel.MEDIUM,
                probability=80,
                impact=50,
                mitigation=f"Install missing tools: {', '.join(missing_tools)}",
                file_paths=[]
            ))
    
    def _analyze_business_risks(self, migration_type: str) -> None:
        """Analyze business risks."""
        # Downtime risk
        self.risks.append(Risk(
            title="Potential Downtime",
            description="Migration may cause service downtime",
            category=RiskCategory.BUSINESS,
            level=RiskLevel.HIGH,
            probability=60,
            impact=80,
            mitigation="Plan migration during low-traffic periods. Use blue-green deployment. Have rollback plan ready.",
            file_paths=[]
        ))
        
        # User experience risk
        self.risks.append(Risk(
            title="User Experience Impact",
            description="Migration may temporarily affect user experience",
            category=RiskCategory.BUSINESS,
            level=RiskLevel.MEDIUM,
            probability=50,
            impact=70,
            mitigation="Communicate changes to users in advance. Provide support during transition. Test thoroughly.",
            file_paths=[]
        ))
    
    def _analyze_compliance_risks(self) -> None:
        """Analyze compliance risks."""
        # Data privacy risk
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'  # Credit card
        ]
        
        files_with_pii = []
        
        for pattern in pii_patterns:
            try:
                for file_path in self.project_path.rglob('*'):
                    if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue']:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if re.search(pattern, content):
                            files_with_pii.append(str(file_path.relative_to(self.project_path)))
            except Exception:
                continue
        
        if files_with_pii:
            self.risks.append(Risk(
                title="PII Data Detected",
                description=f"Found potential personally identifiable information in {len(files_with_pii)} files",
                category=RiskCategory.COMPLIANCE,
                level=RiskLevel.HIGH,
                probability=85,
                impact=90,
                mitigation="Review and secure all PII data. Ensure compliance with GDPR/CCPA. Implement data anonymization.",
                file_paths=files_with_pii[:5]
            ))
    
    def _analyze_dependency_risks(self) -> None:
        """Analyze dependency-related risks."""
        requirements_file = self.project_path / 'requirements.txt'
        
        if requirements_file.exists():
            try:
                content = requirements_file.read_text(encoding='utf-8')
                
                # Check for unpinned versions
                unpinned_deps = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '==' not in line and '>=' not in line and '<=' not in line:
                            unpinned_deps.append(line)
                
                if unpinned_deps:
                    self.risks.append(Risk(
                        title="Unpinned Dependencies",
                        description=f"Found {len(unpinned_deps)} unpinned dependencies",
                        category=RiskCategory.TECHNICAL,
                        level=RiskLevel.MEDIUM,
                        probability=60,
                        impact=65,
                        mitigation="Pin all dependency versions to prevent unexpected breaking changes.",
                        file_paths=['requirements.txt']
                    ))
                        
            except Exception:
                pass
    
    def _get_breaking_change_patterns(self, migration_type: str) -> List[str]:
        """Get breaking change patterns for migration type."""
        patterns = {
            'react-hooks': [
                'componentDidMount', 'componentWillUnmount',
                'componentDidUpdate', 'this.state', 'this.props'
            ],
            'vue3': [
                'Vue.component', 'new Vue', '$on', '$off', '$once'
            ],
            'python3': [
                'print ', 'xrange', 'urllib2', 'raw_input'
            ],
            'typescript': [
                'var ', 'function(', ': any'
            ]
        }
        
        return patterns.get(migration_type, [])
    
    def _find_high_risk_files(self, patterns: List[str]) -> List[str]:
        """Find files with breaking change patterns."""
        high_risk_files = []
        
        for file_path in self.project_path.rglob('*'):
            if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue']:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    pattern_count = sum(content.count(pattern) for pattern in patterns)
                    
                    if pattern_count > 0:
                        high_risk_files.append(str(file_path.relative_to(self.project_path)))
                except Exception:
                    continue
        
        return high_risk_files
    
    def _get_required_tools(self, migration_type: str) -> List[str]:
        """Get required tools for migration type."""
        tools = {
            'react-hooks': ['node', 'npm'],
            'vue3': ['node', 'npm'],
            'python3': ['python3', 'pip3'],
            'typescript': ['node', 'npm', 'typescript'],
            'angular': ['node', 'npm', '@angular/cli'],
            'svelte': ['node', 'npm']
        }
        
        return tools.get(migration_type, [])
    
    def generate_risk_report(self) -> str:
        """
        Generate formatted risk report.
        
        Returns:
            Formatted risk report string
        """
        if not self.risks:
            return "✅ No significant risks detected."
        
        # Group risks by category
        by_category = {}
        for risk in self.risks:
            if risk.category not in by_category:
                by_category[risk.category] = []
            by_category[risk.category].append(risk)
        
        report_lines = [
            "⚠️  MIGRATION RISK ANALYSIS",
            "=" * 50,
            f"Total Risks Identified: {len(self.risks)}",
            ""
        ]
        
        # Summary by level
        level_counts = {level: 0 for level in RiskLevel}
        for risk in self.risks:
            level_counts[risk.level] += 1
        
        report_lines.append("📊 RISK SUMMARY:")
        for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            count = level_counts[level]
            if count > 0:
                emoji = {RiskLevel.CRITICAL: "🔴", RiskLevel.HIGH: "🟠", 
                        RiskLevel.MEDIUM: "🟡", RiskLevel.LOW: "🟢"}[level]
                report_lines.append(f"  {emoji} {level.value}: {count} risks")
        
        report_lines.extend(["", "📋 DETAILED RISKS:", ""])
        
        # Detailed risks by category
        for category in [RiskCategory.SECURITY, RiskCategory.TECHNICAL, 
                        RiskCategory.BUSINESS, RiskCategory.OPERATIONAL, RiskCategory.COMPLIANCE]:
            if category in by_category:
                report_lines.append(f"🏷️  {category.value}:")
                for risk in by_category[category]:
                    risk_score = risk.probability * risk.impact / 100
                    report_lines.extend([
                        f"  🔸 {risk.title} ({risk.level.value})",
                        f"     Risk Score: {risk_score:.0f}/100",
                        f"     Description: {risk.description}",
                        f"     Mitigation: {risk.mitigation}",
                        ""
                    ])
        
        return "\n".join(report_lines)
