import { useEffect, useMemo, useState } from 'react';
import { Activity, Atom, Box, Calculator, ChevronRight, CircleDot, Cpu, Database, FolderKanban, History, Layers3, Orbit, Play, Plus, RefreshCw, ShieldCheck, Square, Waves } from 'lucide-react';
import Visualization3D from './Visualization3D';

const API = 'http://127.0.0.1:8765';
type Page = 'workspace' | 'projects' | 'project' | 'experiment' | 'history' | 'quantum' | 'qft' | 'relativity' | 'blackhole' | 'mathlab' | 'viz3d' | 'validation';
type AnyResult = Record<string, any>;

const nav: { id: Page; label: string; icon: any }[] = [
  { id: 'workspace', label: 'Workspace', icon: Layers3 },
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'history', label: 'Experiment history', icon: History },
  { id: 'quantum', label: 'Quantum mechanics', icon: Atom },
  { id: 'qft', label: 'Quantum field theory', icon: Waves },
  { id: 'relativity', label: 'General relativity', icon: Orbit },
  { id: 'blackhole', label: 'Black-hole physics', icon: CircleDot },
  { id: 'mathlab', label: 'Mathematical laboratory', icon: Calculator },
  { id: 'viz3d', label: '3D visualization studio', icon: Box },
  { id: 'validation', label: 'Validation center', icon: ShieldCheck },
];

function Num({ value }: { value: any }) { return <>{typeof value === 'number' ? Number(value).toPrecision(7) : String(value ?? '')}</>; }
function Metric({ label, value, unit }: { label: string; value: any; unit?: string }) { return <div className="metric"><span>{label}</span><strong><Num value={value} />{unit && <small> {unit}</small>}</strong></div>; }
function Plot({ values, title }: { values: number[]; title: string }) {
  const finite = (values || []).filter(Number.isFinite); if (!finite.length) return null;
  const lo = Math.min(...finite), hi = Math.max(...finite), span = hi - lo || 1;
  const pts = finite.map((v, i) => `${(i / (finite.length - 1 || 1)) * 720},${190 - ((v - lo) / span) * 170}`).join(' ');
  return <div className="plot"><div className="plot-head"><b>{title}</b><span>{lo.toPrecision(4)} — {hi.toPrecision(4)}</span></div><svg viewBox="0 0 720 210" role="img" aria-label={title}><line x1="0" y1="190" x2="720" y2="190" /><polyline points={pts} /></svg></div>;
}
function StatusTag({ status }: { status: string }) {
  const s = (status || '').toLowerCase();
  const cls = s === 'completed' ? 'ok' : s === 'running' || s === 'queued' ? 'run' : s === 'failed' ? 'bad' : 'warn';
  return <span className={`tag ${cls}`}>{status}</span>;
}

async function api(path: string, init?: RequestInit) {
  const r = await fetch(`${API}${path}`, init);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`);
  return d;
}

export default function App() {
  const [page, setPage] = useState<Page>('workspace');
  const [health, setHealth] = useState<AnyResult | null>(null);
  const [connection, setConnection] = useState('Checking local backend…');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [result, setResult] = useState<AnyResult | null>(null);
  const [validation, setValidation] = useState<AnyResult | null>(null);

  // science controls (preserved)
  const [mass, setMass] = useState('1.98847e30'); const [qMass, setQMass] = useState('1'); const [sites, setSites] = useState('64'); const [spacing, setSpacing] = useState('0.25');
  const [r0, setR0] = useState('10'); const [energy, setEnergy] = useState('0.9561828875'); const [angular, setAngular] = useState('3.77964473');
  const [grid, setGrid] = useState('1201'); const [states, setStates] = useState('5'); const [omega, setOmega] = useState('1');
  const [potType, setPotType] = useState('harmonic');
  const [tSteps, setTSteps] = useState('120'); const [tDt, setTDt] = useState('0.02'); const [packetK, setPacketK] = useState('2.0');
  const [barE, setBarE] = useState('0.5'); const [barV, setBarV] = useState('1.0'); const [barL, setBarL] = useState('1.0');
  const [kerrA, setKerrA] = useState('0.5'); const [redR, setRedR] = useState('10');
  const [expr, setExpr] = useState('x**2-2'); const [intExpr, setIntExpr] = useState('x**2'); const [brA, setBrA] = useState('1'); const [brB, setBrB] = useState('2');
  const [vizData, setVizData] = useState<any>(null);

  // phase 1 state
  const [projects, setProjects] = useState<AnyResult[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedProject, setSelectedProject] = useState<AnyResult | null>(null);
  const [projectExperiments, setProjectExperiments] = useState<AnyResult[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<AnyResult | null>(null);
  const [allExperiments, setAllExperiments] = useState<AnyResult[]>([]);
  const [newProject, setNewProject] = useState({ name: '', description: '' });
  const [newExp, setNewExp] = useState({ name: 'Root finding run', description: '', scientific_domain: 'mathematics', model: 'math.root', expression: 'x**2-2', variable: 'x', bracket_a: '1', bracket_b: '2', mass: '1.0', sites: '32', spacing: '0.2', mass_kg: '1.98847e30', omega: '1.0', points: '801', states_count: '3' });
  const [importText, setImportText] = useState('');

  useEffect(() => {
    let alive = true;
    const ping = () => fetch(`${API}/health`).then(r => { if (!r.ok) throw new Error('API unavailable'); return r.json(); }).then(d => { if (alive) { setHealth(d); setConnection(`LOCAL ENGINE ONLINE · ${d.version}`); } }).catch(() => { if (alive) { setHealth(null); setConnection('BACKEND OFFLINE · Start quantumforge-api'); } });
    ping(); const timer = setInterval(ping, 5000); return () => { alive = false; clearInterval(timer); };
  }, []);

  async function refreshProjects(selectId?: string) {
    const d = await api('/projects');
    setProjects(d.projects || []);
    const id = selectId || selectedProjectId || d.projects?.[0]?.id || '';
    if (id) setSelectedProjectId(id);
    return d.projects || [];
  }
  async function loadProject(projectId: string) {
    const d = await api(`/projects/${projectId}`);
    setSelectedProject(d.project); setProjectExperiments(d.experiments || []); setSelectedProjectId(projectId);
  }
  async function loadHistory() { const d = await api('/experiments?limit=100'); setAllExperiments(d.experiments || []); }
  async function loadExperiment(expId: string) { const d = await api(`/experiments/${expId}/detail`); setSelectedExperiment(d); }

  useEffect(() => { if (health) { refreshProjects().then(list => { if (list[0]) loadProject(list[0].id).catch(() => {}); }).catch(() => {}); loadHistory().catch(() => {}); } }, [health]);

  async function request(path: string, body?: AnyResult) {
    setBusy(true); setError(''); setResult(null);
    try { const d = await api(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}); setResult(d); return d; }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); return null; }
    finally { setBusy(false); }
  }
  async function runValidation() {
    setBusy(true); setError('');
    try {
      const [bell, geo, bh] = await Promise.all([
        api('/quantum/density/bell'),
        api('/relativity/schwarzschild/geometry'),
        api('/relativity/schwarzschild', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mass_kg: 1.98847e30 }) }),
      ]);
      setValidation({ bell, geo, bh });
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }

  function expParamsFromForm() {
    if (newExp.model === 'math.root') return { expression: newExp.expression, variable: newExp.variable, bracket: [Number(newExp.bracket_a), Number(newExp.bracket_b)] };
    if (newExp.model === 'quantum.schrodinger.harmonic') return { omega: Number(newExp.omega), points: Number(newExp.points), states: Number(newExp.states_count) };
    if (newExp.model === 'qft.free_scalar_lattice') return { mass: Number(newExp.mass), sites: Number(newExp.sites), spacing: Number(newExp.spacing) };
    if (newExp.model === 'relativity.schwarzschild') return { mass_kg: Number(newExp.mass_kg) };
    if (newExp.model === 'relativity.schwarzschild.geometry') return {};
    return {};
  }

  async function createProject() {
    try { setError(''); await api('/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newProject) }); setNewProject({ name: '', description: '' }); await refreshProjects(); setNotice('Project created.'); setPage('projects'); } catch (e) { setError(String(e)); }
  }
  async function renameProject() {
    if (!selectedProjectId) return;
    const name = prompt('New project name', selectedProject?.name || '');
    if (!name) return;
    await api(`/projects/${selectedProjectId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
    await loadProject(selectedProjectId); await refreshProjects(selectedProjectId);
  }
  async function archiveProject(toggle: boolean) {
    if (!selectedProjectId) return;
    await api(`/projects/${selectedProjectId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ archived: toggle }) });
    await loadProject(selectedProjectId); await refreshProjects(selectedProjectId);
  }
  async function duplicateProject() {
    if (!selectedProjectId) return;
    const d = await api(`/projects/${selectedProjectId}/duplicate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
    await refreshProjects(d.id); await loadProject(d.id); setPage('project');
  }
  async function exportProject() {
    if (!selectedProjectId) return;
    const d = await api(`/projects/${selectedProjectId}/export`);
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `project-${selectedProjectId}.json`; a.click(); URL.revokeObjectURL(a.href);
  }
  async function importProject() {
    try {
      const payload = JSON.parse(importText);
      await api('/projects/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ payload, mode: 'new' }) });
      setImportText(''); await refreshProjects(); await loadHistory(); setNotice('Project imported.');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  async function createExperiment(autoRun: boolean) {
    if (!selectedProjectId) { setError('Select or create a project first.'); return; }
    try {
      setError('');
      const payload = { project_id: selectedProjectId, name: newExp.name, description: newExp.description, scientific_domain: newExp.scientific_domain, model: newExp.model, input_parameters: expParamsFromForm(), input_units: {}, initial_conditions: {}, numerical_method: 'default', solver_configuration: {}, deterministic: false, auto_run: autoRun };
      const d = await api('/experiments/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      await loadProject(selectedProjectId); await loadHistory();
      await loadExperiment(d.experiment.id); setPage('experiment');
      if (autoRun) pollExperiment(d.experiment.id);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  async function runExperiment(expId: string) {
    await api(`/experiments/${expId}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
    pollExperiment(expId);
  }
  async function cancelExperiment(expId: string) { await api(`/experiments/${expId}/cancel`, { method: 'POST' }); await loadExperiment(expId); await loadHistory(); }
  function pollExperiment(expId: string) {
    const t = setInterval(async () => {
      try {
        const d = await api(`/experiments/${expId}/detail`);
        setSelectedExperiment(d);
        const st = d.experiment?.status;
        if (['completed', 'failed', 'cancelled'].includes(st)) { clearInterval(t); if (selectedProjectId) loadProject(selectedProjectId); loadHistory(); }
      } catch { clearInterval(t); }
    }, 600);
  }

  const title = nav.find(n => n.id === page)?.label || (page === 'project' ? 'Project details' : page === 'experiment' ? 'Experiment details' : 'Overview');
  const summary = useMemo(() => health ? `${health.scientific_backend || 'Python'} computation service · schema v${health.schema_version || '?'}` : 'A local Python scientific backend is required for calculations.', [health]);

  return <main className="shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark">QF</div><div><b>QUANTUMFORGE</b><small>SCIENTIFIC WORKSPACE</small></div></div>
      <div className="nav-label">WORKSPACE</div><nav>{nav.map(item => { const Icon = item.icon; return <button key={item.id} className={page === item.id ? 'nav-item selected' : 'nav-item'} onClick={() => { setPage(item.id); setResult(null); setError(''); setNotice(''); if (item.id === 'history') loadHistory(); }}><Icon size={17} /><span>{item.label}</span>{page === item.id && <ChevronRight size={15} />}</button>; })}</nav>
      <div className="side-bottom"><div className={`connection ${health ? 'good' : ''}`}><i />{connection}</div><small>LOCAL COMPUTATION · NO CLOUD UPLOAD</small><small>BUILD 0.4.0 · QUANTUM LAB EXPANSION</small></div>
    </aside>
    <section className="main"><header><div><div className="crumb">QUANTUMFORGE / {title.toUpperCase()}</div><h1>{title}</h1></div><div className="top-state"><span className={health ? 'pulse' : 'pulse down'} />{health ? 'ENGINE CONNECTED' : 'ENGINE DISCONNECTED'}</div></header>
      {notice && <div className="notice"><Database size={19} /><div><b>Status</b><p>{notice}</p></div></div>}
      {error && <div className="error-box">{error}</div>}

      {page === 'workspace' && <>
        <section className="hero"><div className="hero-copy"><div className="eyebrow"><span /> COMPUTE WITH EVIDENCE</div><h2>Scientific project<br /><em>workspace.</em></h2><p>Manage projects and reproducible experiments, then run implemented numerical models across quantum, QFT, and relativity domains. {summary}</p><button className="primary" onClick={() => setPage('projects')}>Open projects <ChevronRight size={16} /></button></div><div className="atom-art"><div className="ring ring-a" /><div className="ring ring-b" /><div className="ring ring-c" /><div className="nucleus">Q</div><i className="electron e1" /><i className="electron e2" /></div></section>
        <div className="workspace-grid">
          <article className="panel"><div className="panel-title"><FolderKanban /><div><small>PROJECTS</small><h3>Recent projects</h3></div></div>
            <div className="list">{projects.slice(0, 6).map(p => <div key={p.id} className="card-row"><div><h4>{p.name}</h4><div className="small">{p.description || 'No description'} · {p.archived ? 'archived' : 'active'}</div></div><button className="secondary" onClick={() => { loadProject(p.id); setPage('project'); }}>Open</button></div>)}{!projects.length && <p className="hint">No projects yet. Create one in Projects.</p>}</div>
          </article>
          <article className="panel"><div className="panel-title"><History /><div><small>HISTORY</small><h3>Recent experiments</h3></div></div>
            <div className="list">{allExperiments.slice(0, 6).map(e => <div key={e.id} className="card-row"><div><h4>{e.name}</h4><div className="small">{e.model} · <StatusTag status={e.status} /></div></div><button className="secondary" onClick={() => { loadExperiment(e.id); setPage('experiment'); }}>View</button></div>)}{!allExperiments.length && <p className="hint">No experiments yet.</p>}</div>
          </article>
        </div>
      </>}

      {page === 'projects' && <>
        <div className="intro"><span className="eyebrow">PROJECT MANAGEMENT / PERSISTENT SQLITE</span><p>Create, rename, duplicate, archive, export, and import projects. Each project contains multiple experiments with versioned metadata.</p></div>
        <div className="split">
          <article className="panel"><div className="panel-title"><Plus /><div><small>CREATE</small><h3>New project</h3></div></div>
            <div className="input-row single"><label>Name<input value={newProject.name} onChange={e => setNewProject({ ...newProject, name: e.target.value })} /></label></div>
            <div className="input-row single"><label>Description<textarea value={newProject.description} onChange={e => setNewProject({ ...newProject, description: e.target.value })} /></label></div>
            <button className="primary" disabled={!health || !newProject.name.trim()} onClick={createProject}>Create project</button>
          </article>
          <article className="panel"><div className="panel-title"><Database /><div><small>IMPORT</small><h3>Import project JSON</h3></div></div>
            <div className="input-row single"><label>Export payload<textarea value={importText} onChange={e => setImportText(e.target.value)} placeholder='Paste exported project JSON...' /></label></div>
            <button className="secondary" disabled={!health || !importText.trim()} onClick={importProject}>Import project</button>
          </article>
        </div>
        <article className="panel"><div className="toolbar"><h3 style={{ margin: 0 }}>All projects</h3><span className="spacer" /><button className="secondary" onClick={() => refreshProjects()}><RefreshCw size={14} /> Refresh</button></div>
          <table className="table"><thead><tr><th>Name</th><th>Description</th><th>Archived</th><th>Updated</th><th></th></tr></thead><tbody>
            {projects.map(p => <tr key={p.id}><td>{p.name}</td><td>{p.description || '—'}</td><td>{p.archived ? 'yes' : 'no'}</td><td className="mono">{p.updated_at}</td><td><button className="link-btn" onClick={() => { loadProject(p.id); setPage('project'); }}>Open</button></td></tr>)}
            {!projects.length && <tr><td colSpan={5} className="hint">No projects.</td></tr>}
          </tbody></table>
        </article>
      </>}

      {page === 'project' && <>
        {!selectedProject ? <article className="panel"><p>Select a project from Projects.</p></article> : <>
          <div className="intro"><span className="eyebrow">PROJECT / {selectedProject.id}</span><p>{selectedProject.description || 'No description.'}</p></div>
          <article className="panel"><div className="toolbar"><h3 style={{ margin: 0 }}>{selectedProject.name}</h3>{selectedProject.archived && <StatusTag status="archived" />}<span className="spacer" />
            <button className="secondary" onClick={renameProject}>Rename</button>
            <button className="secondary" onClick={duplicateProject}>Duplicate</button>
            <button className="secondary" onClick={() => archiveProject(!selectedProject.archived)}>{selectedProject.archived ? 'Unarchive' : 'Archive'}</button>
            <button className="secondary" onClick={exportProject}>Export JSON</button>
          </div>
            <div className="kvs"><b>Schema</b><span>{selectedProject.schema_version}</span><b>Created</b><span className="mono">{selectedProject.created_at}</span><b>Updated</b><span className="mono">{selectedProject.updated_at}</span></div>
          </article>
          <div className="split">
            <article className="panel"><div className="panel-title"><Plus /><div><small>EXPERIMENT</small><h3>Create experiment</h3></div></div>
              <div className="input-row"><label>Name<input value={newExp.name} onChange={e => setNewExp({ ...newExp, name: e.target.value })} /></label><label>Model<select value={newExp.model} onChange={e => setNewExp({ ...newExp, model: e.target.value, scientific_domain: e.target.value.startsWith('quantum') ? 'quantum' : e.target.value.startsWith('qft') ? 'qft' : e.target.value.startsWith('relativity') ? 'relativity' : 'mathematics' })}><option value="math.root">math.root</option><option value="quantum.schrodinger.harmonic">quantum.schrodinger.harmonic</option><option value="qft.free_scalar_lattice">qft.free_scalar_lattice</option><option value="relativity.schwarzschild">relativity.schwarzschild</option><option value="relativity.schwarzschild.geometry">relativity.schwarzschild.geometry</option></select></label></div>
              <div className="input-row single"><label>Description<input value={newExp.description} onChange={e => setNewExp({ ...newExp, description: e.target.value })} /></label></div>
              {newExp.model === 'math.root' && <div className="input-row"><label>Expression<input value={newExp.expression} onChange={e => setNewExp({ ...newExp, expression: e.target.value })} /></label><label>Variable<input value={newExp.variable} onChange={e => setNewExp({ ...newExp, variable: e.target.value })} /></label><label>Bracket a<input value={newExp.bracket_a} onChange={e => setNewExp({ ...newExp, bracket_a: e.target.value })} /></label><label>Bracket b<input value={newExp.bracket_b} onChange={e => setNewExp({ ...newExp, bracket_b: e.target.value })} /></label></div>}
              {newExp.model === 'quantum.schrodinger.harmonic' && <div className="input-row"><label>Omega<input value={newExp.omega} onChange={e => setNewExp({ ...newExp, omega: e.target.value })} /></label><label>Points<input value={newExp.points} onChange={e => setNewExp({ ...newExp, points: e.target.value })} /></label><label>States<input value={newExp.states_count} onChange={e => setNewExp({ ...newExp, states_count: e.target.value })} /></label></div>}
              {newExp.model === 'qft.free_scalar_lattice' && <div className="input-row"><label>Mass<input value={newExp.mass} onChange={e => setNewExp({ ...newExp, mass: e.target.value })} /></label><label>Sites<input value={newExp.sites} onChange={e => setNewExp({ ...newExp, sites: e.target.value })} /></label><label>Spacing<input value={newExp.spacing} onChange={e => setNewExp({ ...newExp, spacing: e.target.value })} /></label></div>}
              {newExp.model === 'relativity.schwarzschild' && <div className="input-row single"><label>Mass (kg)<input value={newExp.mass_kg} onChange={e => setNewExp({ ...newExp, mass_kg: e.target.value })} /></label></div>}
              <div className="panel-actions"><button className="secondary" onClick={() => createExperiment(false)}>Save draft</button><button className="primary" onClick={() => createExperiment(true)}><Play size={14} /> Save & run</button></div>
              <p className="hint">Runs execute via background job service with status/progress tracking and cancellation.</p>
            </article>
            <article className="panel"><div className="panel-title"><History /><div><small>EXPERIMENTS</small><h3>Project experiments</h3></div></div>
              <table className="table"><thead><tr><th>Name</th><th>Model</th><th>Status</th><th></th></tr></thead><tbody>
                {projectExperiments.map(e => <tr key={e.id}><td>{e.name}</td><td className="mono">{e.model}</td><td><StatusTag status={e.status} /></td><td><button className="link-btn" onClick={() => { loadExperiment(e.id); setPage('experiment'); }}>Open</button></td></tr>)}
                {!projectExperiments.length && <tr><td colSpan={4} className="hint">No experiments in this project.</td></tr>}
              </tbody></table>
            </article>
          </div>
        </>}
      </>}

      {page === 'experiment' && <>
        {!selectedExperiment ? <article className="panel"><p>Select an experiment from a project or history.</p></article> : (() => {
          const exp = selectedExperiment.experiment; const job = selectedExperiment.job;
          const progress = Math.round(((exp.execution?.progress || 0) as number) * 100);
          return <>
            <div className="intro"><span className="eyebrow">EXPERIMENT / {exp.id}</span><p>{exp.description || 'No description.'}</p></div>
            <article className="panel"><div className="toolbar"><h3 style={{ margin: 0 }}>{exp.name}</h3><StatusTag status={exp.status} /><span className="spacer" />
              {['queued','running','pending'].includes(exp.status) && <button className="secondary" onClick={() => cancelExperiment(exp.id)}><Square size={14} /> Cancel</button>}
              {!['queued','running'].includes(exp.status) && <button className="primary" onClick={() => runExperiment(exp.id)}><Play size={14} /> Run</button>}
              <button className="secondary" onClick={() => loadExperiment(exp.id)}><RefreshCw size={14} /> Refresh</button>
            </div>
              <div className="progress"><i style={{ width: `${progress}%` }} /></div>
              <p className="hint">Progress: {progress}% · {exp.execution?.status_history?.slice(-1)[0]?.message || ''}</p>
              <div className="kvs"><b>Project</b><span className="mono">{exp.project_id}</span><b>Domain</b><span>{exp.scientific_domain}</span><b>Model</b><span className="mono">{exp.model}</span><b>Numerical method</b><span>{exp.numerical_method}</span><b>Seed</b><span>{exp.seed ?? '—'}</span><b>Software</b><span>{exp.software_version}</span><b>Created</b><span className="mono">{exp.created_at}</span><b>Updated</b><span className="mono">{exp.updated_at}</span><b>Started</b><span className="mono">{exp.started_at || '—'}</span><b>Completed</b><span className="mono">{exp.completed_at || '—'}</span></div>
            </article>
            <div className="split">
              <article className="panel"><h3>Configuration snapshot</h3><div className="kvs"><b>Input parameters</b><pre>{JSON.stringify(exp.input_parameters, null, 2)}</pre><b>Input units</b><pre>{JSON.stringify(exp.input_units, null, 2)}</pre><b>Initial conditions</b><pre>{JSON.stringify(exp.initial_conditions, null, 2)}</pre><b>Solver configuration</b><pre>{JSON.stringify(exp.solver_configuration, null, 2)}</pre><b>Parameter snapshot</b><pre>{JSON.stringify(exp.parameter_snapshot, null, 2)}</pre></div></article>
              <article className="panel"><h3>Execution & provenance</h3><div className="kvs"><b>Execution</b><pre>{JSON.stringify(exp.execution, null, 2)}</pre><b>Provenance</b><pre>{JSON.stringify(exp.provenance, null, 2)}</pre><b>Job</b><pre>{JSON.stringify(job, null, 2)}</pre><b>Error</b><pre>{JSON.stringify(exp.error, null, 2)}</pre></div></article>
            </div>
            <article className="panel"><h3>Result</h3>{exp.result ? <pre>{JSON.stringify(exp.result, null, 2)}</pre> : <p className="hint">No result yet.</p>}</article>
          </>;
        })()}
      </>}

      {page === 'history' && <>
        <div className="intro"><span className="eyebrow">EXPERIMENT HISTORY / REPRODUCIBLE RECORDS</span><p>Global experiment history across projects with status, provenance metadata, and stored results.</p></div>
        <article className="panel"><div className="toolbar"><h3 style={{ margin: 0 }}>All experiments</h3><span className="spacer" /><button className="secondary" onClick={() => loadHistory()}><RefreshCw size={14} /> Refresh</button></div>
          <table className="table"><thead><tr><th>Name</th><th>Project</th><th>Model</th><th>Status</th><th>Updated</th><th></th></tr></thead><tbody>
            {allExperiments.map(e => <tr key={e.id}><td>{e.name}</td><td className="mono">{e.project_id.slice(0, 8)}…</td><td className="mono">{e.model}</td><td><StatusTag status={e.status} /></td><td className="mono">{e.updated_at}</td><td><button className="link-btn" onClick={() => { loadExperiment(e.id); setPage('experiment'); }}>Open</button></td></tr>)}
            {!allExperiments.length && <tr><td colSpan={6} className="hint">No experiments recorded.</td></tr>}
          </tbody></table>
        </article>
      </>}

      {/* Existing scientific labs preserved */}
      {page === 'quantum' && <><div className="intro"><span className="eyebrow">QUANTUM ENGINE / FINITE-DIMENSIONAL + GRID METHODS</span><p>Real numerical solvers: stationary/time-dependent Schrödinger (1D, Crank–Nicolson), tunneling (transfer-matrix), circuits, quantum info and channels. Methods/assumptions returned with results.</p></div><div className="work-grid"><article className="panel"><div className="panel-title"><Atom /><div><small>STATIONARY SCHRÖDINGER</small><h3>1D eigenproblem</h3></div></div><p className="equation">Hψ = Eψ, &nbsp; H = −(ħ²/2m)d²/dx² + V(x)</p><div className="fields"><label>Potential<select value={potType} onChange={e=>setPotType(e.target.value)}><option value="harmonic">Harmonic</option><option value="finite_well">Finite well</option><option value="barrier">Barrier</option><option value="double_well">Double well</option><option value="anharmonic">Anharmonic</option></select></label><label>Grid points<input value={grid} onChange={e => setGrid(e.target.value)} /></label><label>States<input value={states} onChange={e => setStates(e.target.value)} /></label></div><button className="primary" disabled={busy || !health} onClick={() => request('/quantum/schrodinger/harmonic', { potential: { type: potType, omega: Number(omega) }, x_min: -8, x_max: 8, points: Number(grid), states: Number(states) }).then(r=>{ if(r) setVizData({kind:'wave', r}); })}>{busy ? 'Computing…' : 'Run eigensolver ↗'}</button><p className="hint">Dirichlet BC, 2nd-order FD. Custom/swept potentials available via API.</p></article>
      <article className="panel"><div className="panel-title"><Activity /><div><small>TIME-DEPENDENT</small><h3>Crank–Nicolson evolution</h3></div></div><p className="equation">(I + iΔt/2ħ H)ψⁿ⁺¹ = (I − iΔt/2ħ H)ψⁿ</p><div className="fields"><label>Δt<input value={tDt} onChange={e=>setTDt(e.target.value)} /></label><label>Steps<input value={tSteps} onChange={e=>setTSteps(e.target.value)} /></label><label>Packet k₀<input value={packetK} onChange={e=>setPacketK(e.target.value)} /></label></div><button className="secondary" disabled={busy || !health} onClick={() => request('/quantum/schrodinger/evolve', { potential: { type: 'harmonic', omega: 1.0 }, x_min: -10, x_max: 10, points: 301, dt: Number(tDt), steps: Number(tSteps), sample_every: 10, packet: {x0:-3, k0:Number(packetK), sigma:0.5} }).then(r=>{ if(r) setVizData({kind:'evolve', r}); })}>Evolve wavepacket ↗</button><p className="hint">Unconditionally stable linear scheme; norm drift reported.</p></article>
      <article className="panel"><div className="panel-title"><Waves /><div><small>SCATTERING</small><h3>Rectangular barrier tunneling</h3></div></div><p className="equation">T(E), R(E) via transfer-matrix matching (analytic piecewise-constant model)</p><div className="fields"><label>Energy E<input value={barE} onChange={e=>setBarE(e.target.value)} /></label><label>Barrier V₀<input value={barV} onChange={e=>setBarV(e.target.value)} /></label><label>Width L<input value={barL} onChange={e=>setBarL(e.target.value)} /></label></div><button className="secondary" disabled={busy || !health} onClick={() => request('/quantum/tunneling/rectangular', { energy: Number(barE), barrier_height: Number(barV), barrier_width: Number(barL) })}>Compute T/R ↗</button></article>
      <article className="panel"><div className="panel-title"><Cpu /><div><small>QUANTUM INFORMATION</small><h3>States, metrics, channels</h3></div></div><div className="panel-actions"><button className="secondary" disabled={busy || !health} onClick={() => request('/quantum/density/bell')}>Bell density ↗</button><button className="secondary" disabled={busy || !health} onClick={async()=>{ const bell:any = await api('/quantum/density/bell'); setResult(await request('/quantum/info/metrics', { rho_real: bell.real, rho_imag: bell.imag, dims:[2,2], keep:[0] })); }}>Entanglement entropy ↗</button><button className="secondary" disabled={busy || !health} onClick={() => request('/quantum/channel/apply', { real:[[1,0],[0,0]], imag:[[0,0],[0,0]], channel:'depolarizing', p:0.25 })}>Depolarizing channel ↗</button></div><p className="hint">Fidelity, trace distance, partial trace, von Neumann/entanglement entropy, Bloch vector, Kraus channels (bit/phase flip, depolarizing, amplitude/phase damping).</p></article></div></>}
      {page === 'qft' && <><div className="intro"><span className="eyebrow">QUANTUM FIELD THEORY / LATTICE MODEL</span><p>Finite periodic spatial lattice for a free real scalar field in natural units. Interactions and continuum extrapolation are not included.</p></div><article className="panel wide"><div className="panel-title"><Waves /><div><small>GAUSSIAN FIELD THEORY</small><h3>Free scalar field on a 1D lattice</h3></div></div><p className="equation">ω²ₖ = m² + (2/a · sin(πk/N))²</p><div className="fields three"><label>Mass m<input value={qMass} onChange={e => setQMass(e.target.value)} /></label><label>Lattice sites N<input value={sites} onChange={e => setSites(e.target.value)} /></label><label>Spacing a<input value={spacing} onChange={e => setSpacing(e.target.value)} /></label></div><button className="primary" disabled={busy || !health} onClick={() => request('/qft/free-scalar-lattice', { mass: Number(qMass), sites: Number(sites), spacing: Number(spacing) })}>{busy ? 'Computing…' : 'Compute lattice modes ↗'}</button></article></>}
      {page === 'relativity' && <><div className="intro"><span className="eyebrow">GENERAL RELATIVITY / SYMBOLIC DIFFERENTIAL GEOMETRY</span><p>Tensor calculations use the documented Riemann convention and Schwarzschild coordinates (t,r,θ,φ).</p></div><article className="panel wide"><div className="panel-title"><Orbit /><div><small>VACUUM SOLUTION BENCHMARK</small><h3>Schwarzschild metric geometry</h3></div></div><p className="equation">ds² = −(1−2M/r)dt² + (1−2M/r)⁻¹dr² + r²dΩ²</p><button className="primary" disabled={busy || !health} onClick={() => request('/relativity/schwarzschild/geometry')}>{busy ? 'Computing tensors…' : 'Calculate metric tensors ↗'}</button><p className="hint">Returns metric, inverse, determinant, Christoffel symbols, Ricci tensor, Ricci scalar and Einstein tensor. Symbolic calculation may take several seconds.</p></article></>}
      {page === 'blackhole' && <><div className="intro"><span className="eyebrow">BLACK-HOLE PHYSICS / ANALYTIC & NUMERICAL MODELS</span><p>Schwarzschild (exact analytic landmarks, equatorial geodesics) and Kerr equatorial landmarks (analytic formulas). Accretion disk shown as labeled approximate visualization model, not GRMHD/ray-traced physics.</p></div><div className="work-grid"><article className="panel"><div className="panel-title"><CircleDot /><div><small>SCHWARZSCHILD</small><h3>Parameters & redshift</h3></div></div><label className="full-label">Mass (kg)<input value={mass} onChange={e => setMass(e.target.value)} /></label><div className="panel-actions"><button className="primary" disabled={busy || !health} onClick={() => request('/relativity/schwarzschild', { mass_kg: Number(mass) })}>Parameters ↗</button><button className="secondary" disabled={busy || !health} onClick={() => request('/relativity/schwarzschild/redshift?r_over_rs=' + encodeURIComponent(redR))}>Redshift (r/r_s={redR}) ↗</button></div><label className="full-label">r / r_s<input value={redR} onChange={e=>setRedR(e.target.value)} /></label></article>
      <article className="panel"><div className="panel-title"><Orbit /><div><small>KERR (ANALYTIC LANDMARKS)</small><h3>Rotating black hole</h3></div></div><label className="full-label">Spin a = J/M² (0 ≤ a &lt; 1)<input value={kerrA} onChange={e=>setKerrA(e.target.value)} /></label><button className="secondary" disabled={busy || !health} onClick={() => request('/relativity/kerr?spin_a=' + encodeURIComponent(kerrA))}>Compute Kerr landmarks ↗</button><p className="hint">Horizons, equatorial ergosphere, photon orbits, ISCO (pro/retro). No full Kerr geodesic integrator/ray tracing in this build.</p></article>
      <article className="panel"><div className="panel-title"><Activity /><div><small>GEODESIC</small><h3>Equatorial Schwarzschild orbit</h3></div></div><div className="fields"><label>r₀/M<input value={r0} onChange={e => setR0(e.target.value)} /></label><label>E<input value={energy} onChange={e => setEnergy(e.target.value)} /></label><label>L<input value={angular} onChange={e => setAngular(e.target.value)} /></label></div><button className="secondary" disabled={busy || !health} onClick={() => request('/relativity/schwarzschild/geodesic', { r0: Number(r0), energy: Number(energy), angular_momentum: Number(angular), radial_velocity: 0, affine_end: 30, samples: 600, kind: 'timelike' }).then(r=>{ if(r?.coordinates){ const xs=r.coordinates.r.map((rv:number,i:number)=>rv*Math.cos(r.coordinates.phi[i]||0)); const ys=r.coordinates.r.map((rv:number,i:number)=>rv*Math.sin(r.coordinates.phi[i]||0)); setVizData({kind:'orbit', points: xs.map((x:number,i:number)=>({x, y:ys[i], z:0}))}); } })}>Integrate & visualize ↗</button></article></div></>}
      {page === 'validation' && <><div className="intro"><span className="eyebrow">VALIDATION CENTER / REPRODUCIBLE CHECKS</span><p>Run local benchmark checks against exact mathematical identities and known limiting cases. This is software/numerical verification, not independent peer review.</p></div><article className="panel wide"><div className="panel-title"><ShieldCheck /><div><small>BENCHMARK SUITE</small><h3>Built-in scientific checks</h3></div></div><ul className="check-list"><li>Spin-½ Pauli commutators and Hermiticity</li><li>Bell-state density matrix: unit trace, positivity and purity</li><li>Free scalar lattice: positive massive-mode spectrum</li><li>Schwarzschild circular geodesic: four-velocity normalization</li><li>Schwarzschild vacuum metric: Ricci tensor and scalar vanish</li></ul><button className="primary" disabled={busy || !health} onClick={runValidation}>{busy ? 'Running benchmarks…' : 'Run independent identities ↗'}</button><p className="hint">These API benchmark calculations are separate from the pytest suite. No external scientific review has been performed.</p></article></>}

      {page === 'mathlab' && <><div className="intro"><span className="eyebrow">MATHEMATICAL COMPUTATION / SAFE NUMERIC</span><p>Safe symbolic-expression parsing (no unrestricted eval) with numerical solvers. Symbolic algebra, ODE suites, and advanced plotting are partially implemented/roadmapped.</p></div><div className="work-grid"><article className="panel"><div className="panel-title"><Calculator /><div><small>ROOT FINDING</small><h3>Brent–Dekker</h3></div></div><div className="fields"><label>Expression f(x)<input value={expr} onChange={e=>setExpr(e.target.value)} /></label><label>Bracket a<input value={brA} onChange={e=>setBrA(e.target.value)} /></label><label>Bracket b<input value={brB} onChange={e=>setBrB(e.target.value)} /></label></div><button className="primary" disabled={busy||!health} onClick={()=>request('/math/root',{expression:expr,variable:'x',bracket:[Number(brA),Number(brB)]})}>Find root ↗</button></article>
      <article className="panel"><div className="panel-title"><Calculator /><div><small>INTEGRATION</small><h3>Adaptive quadrature</h3></div></div><div className="fields"><label>Expression f(x)<input value={intExpr} onChange={e=>setIntExpr(e.target.value)} /></label><label>Lower<input value={brA} onChange={e=>setBrA(e.target.value)} /></label><label>Upper<input value={brB} onChange={e=>setBrB(e.target.value)} /></label></div><button className="secondary" disabled={busy||!health} onClick={()=>request('/math/integrate',{expression:intExpr,variable:'x',bracket:[Number(brA),Number(brB)]})}>Integrate ↗</button></article></div></>}

      {page === 'viz3d' && <><div className="intro"><span className="eyebrow">3D VISUALIZATION STUDIO / COMPUTED DATA</span><p>Interactive data-driven 3D projection of computed scientific results (orbit trajectories, field/wave surfaces). All geometry derives from solver outputs; no fabricated data. Full WebGL/Three.js pipeline is environment-dependent (dependency availability) with functional projection fallback.</p></div><article className="panel wide"><Visualization3D title={vizData?.kind==='orbit'?'Geodesic orbit (computed)': vizData?.kind==='wave'?'Wavefunction/probability (computed)': 'Scientific 3D view'} points={vizData?.kind==='orbit'?vizData.points: vizData?.kind==='evolve' && vizData.r?.samples?.length ? vizData.r.samples[Math.floor(vizData.r.samples.length/2)].probability_density.map((v:number,i:number)=>({x: vizData.r.x[i], y:v, z:0})) : vizData?.kind==='wave' && vizData.r?.probability_densities?.[0] ? vizData.r.probability_densities[0].map((v:number,i:number)=>({x: vizData.r.x[i], y:v, z:0})) : undefined} note={vizData ? 'Dataset loaded from latest computation.' : 'No dataset loaded. Run a quantum evolution, stationary solve, or geodesic integration and it will be available here.'} /></article></>}

      {result && <section className="result-panel"><div className="result-head"><div><span className="eyebrow">COMPUTATION COMPLETE</span><h3>Numerical result</h3></div><span className="result-tag">REAL SOLVER OUTPUT</span></div>
        {result.energies && <><div className="metrics">{result.energies.slice(0, 4).map((v: number, i: number) => <Metric key={i} label={`E${i}`} value={v} />)}</div><Plot values={result.wavefunctions[0]} title="Ground-state wavefunction ψ₀(x)" /><p className="hint">{result.method} · {result.boundary_condition} · Norm: {result.normalization?.[0]}</p></>}
        {result.schwarzschild_radius_m && <div className="metrics"><Metric label="Schwarzschild radius" value={result.schwarzschild_radius_m} unit="m" /><Metric label="Photon sphere" value={result.photon_sphere_radius_m} unit="m" /><Metric label="ISCO" value={result.isco_radius_m} unit="m" /><Metric label="Hawking temperature" value={result.hawking_temperature_K} unit="K" /></div>}
        {result.mode_frequencies && <><div className="metrics"><Metric label="Lattice vacuum energy" value={result.vacuum_energy_lattice} /><Metric label="Lattice length" value={result.length} /><Metric label="Sites" value={result.sites} /></div><Plot values={result.mode_frequencies} title="Lattice mode frequencies ωₖ" /><p className="hint">{result.approximation} · {result.units}</p></>}
        {result.coordinates && <><div className="metrics"><Metric label="Max normalization error" value={result.max_normalization_error} /><Metric label="Samples" value={result.coordinates.r.length} /><Metric label="Final radius" value={result.coordinates.r.at(-1)} /></div><Plot values={result.coordinates.r} title="Geodesic radial coordinate r(λ)" /><p className="hint">{result.method} · {result.termination}</p></>}
        {result.ricci_scalar !== undefined && <><div className="metrics"><Metric label="Metric determinant" value={result.determinant} /><Metric label="Ricci scalar" value={result.ricci_scalar} /><Metric label="Coordinates" value={result.coordinates.join(', ')} /></div><p className="hint">Riemann convention: {result.convention}</p><details><summary>Christoffel symbols (all components)</summary><pre>{JSON.stringify(result.christoffel_symbols, null, 2)}</pre></details></>}
        {result.diagnostics && <div className="metrics"><Metric label="Physical density matrix" value={String(result.diagnostics.valid_density_matrix)} /><Metric label="Trace" value={result.diagnostics.trace_real} /><Metric label="Purity" value={result.diagnostics.purity} /><Metric label="Minimum eigenvalue" value={result.diagnostics.minimum_eigenvalue} /></div>}
        <details><summary>Raw reproducible JSON</summary><pre>{JSON.stringify(result, null, 2)}</pre></details>
      </section>}
      {validation && <section className="result-panel"><div className="result-head"><div><span className="eyebrow">IDENTITY CHECKS</span><h3>Benchmark observations</h3></div><span className="result-tag">COMPUTED NOW</span></div><div className="metrics"><Metric label="Bell density valid" value={String(validation.bell.diagnostics.valid_density_matrix)} /><Metric label="Bell purity" value={validation.bell.diagnostics.purity} /><Metric label="Schwarzschild Ricci scalar" value={validation.geo.ricci_scalar} /><Metric label="Solar-mass rₛ (m)" value={validation.bh.schwarzschild_radius_m} /></div><p className="hint">Schwarzschild Ricci tensor: {JSON.stringify(validation.geo.ricci_tensor)}. These are built-in verification cases, not independent review.</p></section>}
      <footer>QUANTUMFORGE 0.4.0 · MODELS ARE FINITE AND EXPLICIT · SCIENTIFIC CLAIMS REQUIRE VALIDATION</footer>
    </section>
  </main>;
}
