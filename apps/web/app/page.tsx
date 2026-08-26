"use client";
import {useMemo,useState} from 'react';

type Node = {id:string,name:string,intent:string,classification:string,agentization_score:number,risk:string,confidence:number,rationale:string,target_type:string,model_profile?:string|null,requires_approval:boolean,user_override:boolean};
type Plan = {project_name:string,migration_confidence:number,approved:boolean,nodes:Node[],warnings:string[]};
const API=process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export default function Home(){
 const [path,setPath]=useState('../../examples/uipath-invoice');
 const [projectId,setProjectId]=useState('');
 const [plan,setPlan]=useState<Plan|null>(null);
 const [busy,setBusy]=useState(false);
 const [msg,setMsg]=useState('');
 async function importAnalyze(){setBusy(true);setMsg('');try{let r=await fetch(`${API}/projects/import`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({path})});let j=await r.json();if(!r.ok)throw new Error(j.detail||'Import failed');setProjectId(j.project_id);r=await fetch(`${API}/projects/${j.project_id}/analyze`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({strategy:'balanced'})});j=await r.json();if(!r.ok)throw new Error(j.detail||'Analysis failed');setPlan(j.plan);}catch(e:any){setMsg(e.message)}finally{setBusy(false)}}
 async function patch(n:Node, classification:string){if(!projectId)return;let r=await fetch(`${API}/projects/${projectId}/plan`,{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({node_id:n.id,classification,target_type:classification==='REASON'?'agent':classification==='TOOLIFY'?'tool':classification==='HUMANIZE'?'human':'deterministic'})});let j=await r.json();if(r.ok)setPlan(j);else setMsg(j.detail||'Update failed')}
 async function approve(){let r=await fetch(`${API}/projects/${projectId}/approve`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({reviewer:'review-studio-user',role:'admin',approved:true,comment:'Approved in Review Studio'})});let j=await r.json();if(r.ok)setPlan(j);else setMsg(j.detail||'Approval failed')}
 const counts=useMemo(()=>{let c:Record<string,number>={};plan?.nodes.forEach(n=>c[n.classification]=(c[n.classification]||0)+1);return c},[plan]);
 return <main>
  <header><div><div className="eyebrow">OPEN-SOURCE MIGRATION COMPILER</div><h1>RPA2APA Review Studio</h1><p>Understand. Review. Govern. Then agentize.</p></div><div className="score">{plan?<><strong>{plan.migration_confidence}%</strong><span>migration confidence</span></>:<><strong>APA</strong><span>human-reviewed conversion</span></>}</div></header>
  <section className="import"><input value={path} onChange={e=>setPath(e.target.value)} aria-label="UiPath project path"/><button onClick={importAnalyze} disabled={busy}>{busy?'Analyzing…':'Import & Analyze'}</button></section>
  {msg&&<div className="error">{msg}</div>}
  {plan&&<>
   <section className="stats">{Object.entries(counts).map(([k,v])=><div className="stat" key={k}><b>{v}</b><span>{k}</span></div>)}</section>
   <section className="reviewHead"><div><div className="eyebrow">MIGRATION PLAN</div><h2>{plan.project_name}</h2><p>Review every proposed semantic change. Your override becomes part of migration traceability.</p></div><button className="approve" onClick={approve} disabled={plan.approved}>{plan.approved?'Plan Approved':'Approve Migration Plan'}</button></section>
   <div className="grid">{plan.nodes.map((n,i)=><article className={`node risk-${n.risk.toLowerCase()}`} key={n.id}>
    <div className="nodeTop"><span className="index">{String(i+1).padStart(2,'0')}</span><span className={`pill ${n.classification.toLowerCase()}`}>{n.classification}</span><span className="risk">{n.risk}</span></div>
    <h3>{n.name}</h3><p className="intent">{n.intent}</p><p className="reason">{n.rationale}</p>
    <div className="meters"><label>Agentization <b>{n.agentization_score}</b><meter min="0" max="100" value={n.agentization_score}/></label><label>Confidence <b>{Math.round(n.confidence*100)}%</b><meter min="0" max="100" value={n.confidence*100}/></label></div>
    <div className="meta"><span>Target: {n.target_type}</span><span>{n.model_profile?`Model: ${n.model_profile}`:'No LLM'}</span><span>{n.requires_approval?'Runtime approval':'No runtime gate'}</span></div>
    <select value={n.classification} onChange={e=>patch(n,e.target.value)}><option>KEEP</option><option>TOOLIFY</option><option>REASON</option><option>HUMANIZE</option><option>RETIRE</option><option>MANUAL_REVIEW</option></select>
   </article>)}</div>
  </>}
 </main>
}
