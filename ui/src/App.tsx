import { useState, useRef, useEffect } from 'react';

// --- Types ---
type View = 'dashboard' | 'migration' | 'compliance' | 'plugins';
type LogLevel = 'debug' | 'info' | 'success' | 'warning' | 'error';
type AppStatus = 'idle' | 'running' | 'success' | 'error';

interface LogEntry {
    timestamp: string;
    text: string;
    level: LogLevel;
}

interface OperationResult {
    total_candidates?: number;
    changed_files?: number;
    dry_run?: boolean;
    candidates?: string[];
    results?: Array<{ file: string; changed?: boolean; applied?: boolean; error?: string; diff?: string }>;
    total_findings?: number;
    files_with_pii?: number;
    findings?: Array<{ file_path: string; line: number; type: string; severity: string; match: string }>;
    error?: { message?: string };
}

// --- Icons (SVG) ---
const LayoutIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>;
const PlayIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>;
const ShieldIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>;
const PackageIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>;
const SettingsIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>;
const CpuIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="15" x2="23" y2="15"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="15" x2="4" y2="15"></line></svg>;

function App() {
    const [activeView, setActiveView] = useState<View>('dashboard');
    const [theme, setTheme] = useState<'dark' | 'light'>('dark');
    const [status, setStatus] = useState<AppStatus>('idle');
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

    // App State
    const [targetPath, setTargetPath] = useState<string>('./my-project');
    const [migrationType, setMigrationType] = useState<string>('react-hooks');
    const [isDryRun, setIsDryRun] = useState<boolean>(true);
    const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('shiftiq-api-key') || '');

    // Metrics (Derived/Active)
    const [filesScanned, setFilesScanned] = useState<number>(0);
    const [filesMigrated, setFilesMigrated] = useState<number>(0);
    const [issuesFound, setIssuesFound] = useState<number>(0);
    const [piiFindings, setPiiFindings] = useState<number>(0);
    const [securityViolations, setSecurityViolations] = useState<number>(0);

    const consoleEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Layout Side Effects
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    useEffect(() => {
        if (consoleEndRef.current) {
            consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    useEffect(() => {
        localStorage.setItem('shiftiq-api-key', apiKey);
    }, [apiKey]);

    // Core Actions
    const addLog = (text: string, level: LogLevel = 'info') => {
        const timestamp = new Date().toISOString().substring(11, 19);
        setLogs(prev => [...prev, { timestamp, text, level }]);

        if (text.includes("Found candidate") || text.includes("Scanning")) setFilesScanned(prev => prev + 1);
        if (text.includes("Migrated:")) setFilesMigrated(prev => prev + 1);
        if (level === 'error' || text.includes("Security Error")) setIssuesFound(prev => prev + 1);
        if (text.includes("PII") || text.includes("Pattern")) setPiiFindings(prev => prev + 1);
        if (text.includes("Sandbox") || text.includes("Path Violation")) setSecurityViolations(prev => prev + 1);
    };

    const requestJson = async (endpoint: string, body: Record<string, unknown>): Promise<OperationResult> => {
        const controller = new AbortController();
        abortControllerRef.current = controller;
        const response = await fetch(`${apiBaseUrl}/api/v1${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(apiKey ? { 'X-API-Key': apiKey } : {}),
            },
            body: JSON.stringify(body),
            signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = payload?.error?.message || `API request failed with ${response.status}`;
            throw new Error(message);
        }
        return payload;
    };

    const summarizeResult = (action: 'analyze' | 'run' | 'compliance', result: OperationResult) => {
        if (action === 'analyze') {
            const candidates = result.candidates || [];
            setFilesScanned(candidates.length);
            addLog(`Scan complete. Found ${result.total_candidates ?? candidates.length} candidate files.`, candidates.length ? 'success' : 'warning');
            candidates.slice(0, 50).forEach(file => addLog(`Candidate: ${file}`, 'info'));
            if (candidates.length === 0) addLog('No migration candidates were found for the selected type.', 'warning');
        }
        if (action === 'run') {
            const results = result.results || [];
            setFilesMigrated(results.filter(item => item.applied).length);
            addLog(`${result.dry_run ? 'Dry run' : 'Migration'} complete. ${result.changed_files ?? 0} files would change.`, 'success');
            results.slice(0, 50).forEach(item => {
                if (item.error) addLog(`${item.file}: ${item.error}`, 'error');
                else if (item.changed) addLog(`${item.applied ? 'Applied' : 'Would change'}: ${item.file}`, 'success');
                else addLog(`Unchanged: ${item.file}`, 'info');
            });
            if (results.length === 0) addLog('No matching files were found.', 'warning');
        }
        if (action === 'compliance') {
            const findings = result.findings || [];
            setPiiFindings(result.total_findings || 0);
            addLog(`Pattern scan complete. ${result.total_findings || 0} findings across ${result.files_with_pii || 0} files.`, findings.length ? 'warning' : 'success');
            findings.slice(0, 50).forEach(finding => addLog(`${finding.file_path}:${finding.line} ${finding.type} ${finding.severity} ${finding.match}`, 'warning'));
        }
    };

    const startAction = async (action: 'analyze' | 'run' | 'compliance') => {
        if (status === 'running') return;
        setLogs([]);
        setFilesScanned(0);
        setFilesMigrated(0);
        setIssuesFound(0);
        setPiiFindings(0);
        setSecurityViolations(0);
        setStatus('running');

        if (abortControllerRef.current) abortControllerRef.current.abort();
        addLog(`[System] Initiating ${action} sequence for ${migrationType}`, 'debug');

        if (!apiKey.trim()) {
            addLog('Missing API key. Set the API key before running protected operations.', 'error');
            setStatus('error');
            return;
        }

        try {
            const result = action === 'compliance'
                ? await requestJson('/compliance/scan', { path: targetPath })
                : await requestJson(action === 'run' ? '/run' : '/analyze', {
                    path: targetPath,
                    migration_type: migrationType,
                    dry_run: isDryRun,
                    include_confidence: action === 'analyze',
                });
            summarizeResult(action, result);
            setStatus('success');
            addLog(`=== ${action.toUpperCase()} COMPLETE ===`, 'debug');
        } catch (error) {
            const message = error instanceof Error ? error.message : 'API unavailable';
            addLog(message, 'error');
            setStatus('error');
        }
    };

    const cancelAction = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            setStatus('idle');
            addLog("[System] Sequence terminated by operator.", 'warning');
        }
    };

    // --- Sub-Views ---

    const DashboardView = () => (
        <div className="view-container fade-in">
            <div className="stats-grid">
                <div className="glass-card">
                    <div className="stat-header">
                        <div className="stat-icon" style={{ background: 'rgba(15, 118, 110, 0.1)', color: 'var(--primary)' }}>
                            <LayoutIcon />
                        </div>
                        {filesMigrated > 0 && <span className="badge badge-success">+2.4%</span>}
                    </div>
                    <div className="stat-value">{filesMigrated > 0 ? "84%" : "--"}</div>
                    <div className="stat-label">Avg. Confidence Score</div>
                    <div style={{ marginTop: '1rem', height: '30px', width: '100%', opacity: 0.3 }}>
                        <svg viewBox="0 0 100 30" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
                            <path d="M0,25 L20,20 L40,28 L60,10 L80,15 L100,5" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </div>
                </div>
                <div className="glass-card">
                    <div className="stat-header">
                        <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--emerald)' }}>
                            <PackageIcon />
                        </div>
                    </div>
                    <div className="stat-value">{filesScanned > 0 ? (filesScanned * 12).toLocaleString() : "0"}</div>
                    <div className="stat-label">Approx. LoC Analyzed</div>
                    <div style={{ marginTop: '1rem', height: '30px', width: '100%', opacity: 0.3 }}>
                        <svg viewBox="0 0 100 30" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
                            <path d="M0,28 L20,25 L40,20 L60,22 L80,18 L100,15" fill="none" stroke="var(--emerald)" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </div>
                </div>
                <div className="glass-card">
                    <div className="stat-header">
                        <div className="stat-icon" style={{ background: 'rgba(244, 63, 94, 0.1)', color: 'var(--rose)' }}>
                            <ShieldIcon />
                        </div>
                    </div>
                    <div className="stat-value">{issuesFound}</div>
                    <div className="stat-label">Security Flags</div>
                    <div style={{ marginTop: '1rem', height: '30px', width: '100%', opacity: 0.3 }}>
                        <svg viewBox="0 0 100 30" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
                            <path d="M0,15 L20,18 L40,15 L60,25 L80,22 L100,28" fill="none" stroke="var(--rose)" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </div>
                </div>
            </div>

            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
                {filesScanned === 0 ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ color: 'var(--text-dim)', marginBottom: '1rem' }}><CpuIcon /></div>
                        <h3>No Live Telemetry</h3>
                        <p style={{ maxWidth: '400px', margin: '1rem auto' }}>Connect to a project in the Migration Engine to start streaming architectural insights and risk scores.</p>
                        <button className="btn btn-secondary" style={{ width: 'auto' }} onClick={() => setActiveView('migration')}>Go to Migration Engine</button>
                    </div>
                ) : (
                    <div style={{ width: '100%' }}>
                        <h3 style={{ marginBottom: '1.5rem' }}>Active Session Activity</h3>
                        <div className="log-entry" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                            <span className="log-time">{new Date().toISOString().substring(11, 16)}</span>
                            <div className="log-msg info">System initialized. Last scan processed {filesScanned} nodes. {filesMigrated} mutations pending application.</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );


    const MigrationView = () => (
        <div className="view-container">
            <div className="console-section">
                <div className="config-panel">
                    <div className="glass-card">
                        <h3 style={{ marginBottom: '1.5rem' }}>Configuration</h3>
                        <div className="input-group" style={{ marginBottom: '1.25rem' }}>
                            <label className="input-label">Project Ingress Path</label>
                            <input
                                className="input-field"
                                value={targetPath}
                                onChange={e => setTargetPath(e.target.value)}
                                placeholder="/var/www/my-app"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: '1.25rem' }}>
                            <label className="input-label">API Key</label>
                            <input
                                className="input-field"
                                type="password"
                                value={apiKey}
                                onChange={e => setApiKey(e.target.value)}
                                placeholder="Set MIGRATION_API_KEY"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: '1.25rem' }}>
                            <label className="input-label">Engine Standard</label>
                            <select
                                className="input-field"
                                value={migrationType}
                                onChange={e => setMigrationType(e.target.value)}
                            >
                                <option value="react-hooks">React: Class → Hooks (Standard)</option>
                                <option value="vue3">Vue: v2 → v3 Composition</option>
                                <option value="python3">Python: v2.7 → v3.x Legacy</option>
                            </select>
                        </div>

                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginBottom: '1.5rem' }}>
                            <input
                                type="checkbox"
                                checked={isDryRun}
                                onChange={e => setIsDryRun(e.target.checked)}
                                style={{ width: '16px', height: '16px', accentColor: 'var(--primary)' }}
                            />
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>Dry Run (Validation Only)</span>
                        </label>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {status === 'running' ? (
                                <button className="btn btn-danger" onClick={cancelAction}>Terminate Signal</button>
                            ) : (
                                <>
                                    <button className="btn btn-secondary" onClick={() => startAction('analyze')}>Dry-Run Analyze</button>
                                    <button className="btn btn-primary" onClick={() => startAction('run')}>Execute Migration</button>
                                    <button className="btn btn-secondary" onClick={() => startAction('compliance')}>Pattern Scan</button>
                                </>
                            )}
                        </div>
                    </div>

                    <div className="glass-card" style={{ border: '1px solid var(--border-glass)', background: 'transparent' }}>
                        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '1rem' }}>Active Telemetry</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-dim)' }}>Scanned Nodes</span>
                                <span style={{ fontWeight: 600 }}>{filesScanned}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-dim)' }}>Mutations</span>
                                <span style={{ fontWeight: 600, color: 'var(--emerald)' }}>{filesMigrated}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-dim)' }}>Anomalies</span>
                                <span style={{ fontWeight: 600, color: issuesFound > 0 ? 'var(--rose)' : 'inherit' }}>{issuesFound}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="console-container">
                    <div className="console-header">
                        <div className="console-tabs">
                            <div className="tab active">output.stream</div>
                            <div className="tab">diagnostics.json</div>
                        </div>
                        {status === 'running' && <div className="pulse"></div>}
                    </div>
                    <div className="console-body">
                        {logs.length === 0 ? (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#333' }}>
                                Awaiting mission parameters...
                            </div>
                        ) : (
                            logs.map((log, idx) => (
                                <div key={idx} className="log-entry">
                                    <span className="log-time">{log.timestamp}</span>
                                    <div className={`log-msg ${log.level}`}>{log.text}</div>
                                </div>
                            ))
                        )}
                        <div ref={consoleEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );

    const ComplianceView = () => (
        <div className="view-container fade-in">
            <div className="glass-card" style={{ maxWidth: '800px' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Pattern Scanner</h3>
                <p style={{ marginBottom: '2rem' }}>PII/PHI/PCI-oriented pattern findings from the last local scan.</p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{
                        background: piiFindings > 0 ? 'rgba(244, 63, 94, 0.05)' : 'rgba(16, 185, 129, 0.05)',
                        border: piiFindings > 0 ? '1px solid rgba(244, 63, 94, 0.1)' : '1px solid rgba(16, 185, 129, 0.1)',
                        padding: '1.25rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '1rem'
                    }}>
                        <div style={{ color: piiFindings > 0 ? 'var(--rose)' : 'var(--emerald)' }}><ShieldIcon /></div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600 }}>PII/PHI/PCI Pattern Scanner</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                                {piiFindings === 0 ? "Zero PII findings across current metadata." : `Flagged ${piiFindings} potential PII patterns.`}
                            </div>
                        </div>
                        <span className={`badge ${piiFindings === 0 ? 'badge-success' : 'badge-warning'}`}>
                            {piiFindings === 0 ? 'Passed' : 'Review Required'}
                        </span>
                    </div>

                    <div style={{
                        background: securityViolations > 0 ? 'rgba(244, 63, 94, 0.05)' : 'rgba(16, 185, 129, 0.05)',
                        border: securityViolations > 0 ? '1px solid rgba(244, 63, 94, 0.1)' : '1px solid rgba(16, 185, 129, 0.1)',
                        padding: '1.25rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '1rem'
                    }}>
                        <div style={{ color: securityViolations > 0 ? 'var(--rose)' : 'var(--emerald)' }}><ShieldIcon /></div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600 }}>Sandbox Integrity</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                                {securityViolations === 0 ? "All file operations restricted to safe boundaries." : `Detected ${securityViolations} unauthorized path attempts.`}
                            </div>
                        </div>
                        <span className={`badge ${securityViolations === 0 ? 'badge-success' : 'badge-warning'}`}>
                            {securityViolations === 0 ? 'Passed' : 'Violation'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );


    return (
        <div className="app-shell">
            {/* Sidebar Nav */}
            <aside className="sidebar">
                <div className="brand">
                    <div className="logo-icon">C</div>
                    <div className="brand-text">
                        <h1>Code Migration</h1>
                        <p>Local Workbench</p>
                    </div>
                </div>

                <nav className="nav-menu">
                    <div className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveView('dashboard')}>
                        <LayoutIcon /> Dashboard
                    </div>
                    <div className={`nav-item ${activeView === 'migration' ? 'active' : ''}`} onClick={() => setActiveView('migration')}>
                        <PlayIcon /> Migration Engine
                    </div>
                    <div className={`nav-item ${activeView === 'compliance' ? 'active' : ''}`} onClick={() => setActiveView('compliance')}>
                        <ShieldIcon /> Pattern Scanner
                    </div>
                    <div className={`nav-item ${activeView === 'plugins' ? 'active' : ''}`} onClick={() => setActiveView('plugins')}>
                        <PackageIcon /> Registry Tools
                    </div>
                </nav>

                <div style={{ marginTop: 'auto' }}>
                    <div className="nav-item" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}>
                        <SettingsIcon /> {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                    </div>
                </div>
            </aside>

            {/* Content Area */}
            <main className="main-area">
                <header className="header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <CpuIcon />
                        <div>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>SYSTEM_NODE_01</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status: {status.toUpperCase()}</div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Operator_Admin</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Security Level: HIGH</div>
                        </div>
                        <div style={{ width: '40px', height: '40px', background: 'var(--border-glass)', borderRadius: '8px' }}></div>
                    </div>
                </header>

                {activeView === 'dashboard' && <DashboardView />}
                {activeView === 'migration' && <MigrationView />}
                {activeView === 'compliance' && <ComplianceView />}
                {activeView === 'plugins' && (
                    <div className="view-container">
                        <div className="glass-card">
                            <h3>Registry Tools</h3>
                            <p>Scan and manage installed migration plugins.</p>
                            <div style={{ marginTop: '2rem', padding: '2rem', border: '1px dashed var(--border-glass)', borderRadius: '8px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                Feature under active development.
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
