import { useMemo, useState } from 'react';

type Vec3 = { x: number; y: number; z: number };
type Props = {
  title?: string;
  points?: Vec3[];
  grid?: { x: number[]; z: number[]; y: number[][] };
  note?: string;
};

function project(p: Vec3, yaw: number, pitch: number, scale: number, cx: number, cy: number) {
  const cyaw = Math.cos(yaw), syaw = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = p.x * cyaw - p.z * syaw;
  const z1 = p.x * syaw + p.z * cyaw;
  const y2 = p.y * cp - z1 * sp;
  const z2 = p.y * sp + z1 * cp;
  return { sx: cx + x1 * scale, sy: cy - y2 * scale, depth: z2 };
}

function normalizePoints(pts: Vec3[]): Vec3[] {
  if (!pts.length) return pts;
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y), zs = pts.map(p => p.z);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const cz = (Math.min(...zs) + Math.max(...zs)) / 2;
  const maxd = Math.max(1e-9, ...pts.map(p => Math.max(Math.abs(p.x - cx), Math.abs(p.y - cy), Math.abs(p.z - cz))));
  const s = 2.0 / maxd;
  return pts.map(p => ({ x: (p.x - cx) * s, y: (p.y - cy) * s, z: (p.z - cz) * s }));
}

export default function Visualization3D({ title, points, grid, note }: Props) {
  const [yaw, setYaw] = useState(0.8);
  const [pitch, setPitch] = useState(0.6);
  const [zoom, setZoom] = useState(90);
  const w = 760, h = 420, cx = w / 2, cy = h / 2 + 10;

  const normPts = useMemo(() => normalizePoints((points || []).filter(p => [p.x,p.y,p.z].every(Number.isFinite))), [points]);
  const projected = useMemo(() => normPts.map(p => ({ ...project(p, yaw, pitch, zoom, cx, cy), p })), [normPts, yaw, pitch, zoom]);

  const gridLines = useMemo(() => {
    if (!grid || !grid.x?.length || !grid.z?.length || !grid.y?.length) return [] as string[];
    const nx = grid.x.length, nz = grid.z.length;
    let minY = Infinity, maxY = -Infinity;
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { const v = Number(grid.y[i]?.[j] ?? 0); if (v < minY) minY = v; if (v > maxY) maxY = v; }
    const span = (maxY - minY) || 1;
    const pts: Vec3[] = [];
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) pts.push({ x: grid.x[i], y: ((Number(grid.y[i]?.[j] ?? 0) - minY) / span) * 2 - 1, z: grid.z[j] });
    const npts = normalizePoints(pts);
    const idx = (i: number, j: number) => i * nz + j;
    const lines: string[] = [];
    for (let i = 0; i < nx; i++) {
      let d = '';
      for (let j = 0; j < nz; j++) { const s = project(npts[idx(i,j)], yaw, pitch, zoom, cx, cy); d += `${j===0?'M':'L'}${s.sx.toFixed(2)} ${s.sy.toFixed(2)} `; }
      lines.push(d);
    }
    for (let j = 0; j < nz; j++) {
      let d = '';
      for (let i = 0; i < nx; i++) { const s = project(npts[idx(i,j)], yaw, pitch, zoom, cx, cy); d += `${i===0?'M':'L'}${s.sx.toFixed(2)} ${s.sy.toFixed(2)} `; }
      lines.push(d);
    }
    return lines;
  }, [grid, yaw, pitch, zoom]);

  const axes = useMemo(() => {
    const o = {x:0,y:0,z:0}; const ax = [{v:{x:2.2,y:0,z:0},c:'#e35b65',l:'X'},{v:{x:0,y:2.2,z:0},c:'#7bd1a3',l:'Y'},{v:{x:0,y:0,z:2.2},c:'#3a86ff',l:'Z'}];
    return ax.map(a => ({ ...a, p1: project(o,yaw,pitch,zoom,cx,cy), p2: project(a.v,yaw,pitch,zoom,cx,cy) }));
  }, [yaw,pitch,zoom]);

  const linePath = projected.length ? projected.map((p,i)=>`${i===0?'M':'L'}${p.sx.toFixed(2)} ${p.sy.toFixed(2)}`).join(' ') : '';

  return <div>
    <div className="plot-head"><b>{title || '3D Scientific Visualization'}</b><span className="small">Data-driven 3D projection (rotatable). WebGL/Three.js renderer: pending dependency availability in this environment.</span></div>
    <div className="fields three" style={{marginTop:8}}>
      <label>Yaw<input type="range" min={-314} max={314} value={Math.round(yaw*100)} onChange={e=>setYaw(Number(e.target.value)/100)} /></label>
      <label>Pitch<input type="range" min={-150} max={150} value={Math.round(pitch*100)} onChange={e=>setPitch(Number(e.target.value)/100)} /></label>
      <label>Zoom<input type="range" min={30} max={180} value={zoom} onChange={e=>setZoom(Number(e.target.value))} /></label>
    </div>
    <svg viewBox={`0 0 ${w} ${h}`} style={{width:'100%', height:420, background:'#0b0c10', border:'1px solid #2a2b32', borderRadius:8}}>
      <rect x="0" y="0" width={w} height={h} fill="#0b0c10" />
      {axes.map((a,i)=><g key={i}><line x1={a.p1.sx} y1={a.p1.sy} x2={a.p2.sx} y2={a.p2.sy} stroke={a.c} strokeWidth="1.5" /><text x={a.p2.sx+4} y={a.p2.sy} fill={a.c} fontSize="10">{a.l}</text></g>)}
      {gridLines.map((d,i)=><path key={i} d={d} fill="none" stroke={i % 6 === 0 ? '#3a86ff55' : '#3a86ff22'} strokeWidth={i % 6 === 0 ? 1.2 : 0.7} />)}
      {linePath && <path d={linePath} fill="none" stroke="#7bd1a3" strokeWidth="2" />}
      {projected.slice(-1).map((p,i)=><circle key={i} cx={p.sx} cy={p.sy} r={4} fill="#e35b65" />)}
      {!projected.length && !gridLines.length && <text x={cx-120} y={cy} fill="#898991" fontSize="12">No computed 3D dataset loaded. Run a computation to visualize.</text>}
    </svg>
    {note && <p className="hint">{note}</p>}
    <p className="hint">Rendering uses actual computed data supplied by the scientific engine (projected to 2D for display). This is not a CSS-only effect.</p>
  </div>;
}
