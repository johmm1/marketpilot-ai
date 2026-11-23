'use client';
import {useEffect,useState} from 'react';
type Provider={id:string;name:string;category:string;integration_type:string;auth_type:string;environments:string[];capabilities:string[];setup_required:string[];official_docs:string;status:string};
type Probe={provider:string;reachable:boolean|null;status?:string;scope:string;message?:string;environment?:string;error?:string;live_trading_enabled:boolean};
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
export default function BrokerConnections(){
 const [providers,setProviders]=useState<Provider[]>([]);
 const [results,setResults]=useState<Record<string,Probe>>({});
 const [busy,setBusy]=useState<string|null>(null);
 useEffect(()=>{fetch(API+'/api/brokers/providers').then(r=>r.json()).then(d=>setProviders(d.providers||[])).catch(()=>setProviders([]))},[]);
 async function probe(id:string){setBusy(id);try{const r=await fetch(API+'/api/brokers/probe/'+id,{cache:'no-store'});const d=await r.json();setResults(v=>({...v,[id]:d}))}catch{setResults(v=>({...v,[id]:{provider:id,reachable:false,scope:'probe_failed',error:'API unavailable',live_trading_enabled:false}}))}finally{setBusy(null)}}
 return <section className="panel p-4 mt-5"><div className="flex flex-wrap justify-between gap-3"><div><h2 className="font-bold">Broker connections</h2><p className="muted text-sm mt-1">Multi-provider foundation · official API routes only</p></div><span className="text-xs rounded-full border border-amber-500/50 px-3 py-1 text-amber-200">Live execution locked</span></div>
 <div className="grid md:grid-cols-3 gap-3 mt-4">{providers.map(p=>{const result=results[p.id];return <article key={p.id} className="rounded-xl border border-slate-700 p-3"><div className="flex justify-between gap-2"><b>{p.name}</b><span className="text-[10px] muted">{result?.reachable===true?'REACHABLE':result?.reachable===false?'OFFLINE':p.status.replaceAll('_',' ').toUpperCase()}</span></div><p className="muted text-xs mt-2">{p.integration_type.replaceAll('_',' ')}</p><p className="text-xs mt-3">Capabilities: {p.capabilities.join(' · ')}</p><ul className="muted text-xs list-disc pl-4 mt-3 space-y-1">{p.setup_required.map(s=><li key={s}>{s}</li>)}</ul>{result&&<p className="text-xs mt-3 rounded-lg bg-slate-950 p-2">{result.message||result.scope.replaceAll('_',' ')}{result.environment?' · '+result.environment:''}{result.error?' · '+result.error:''}</p>}<div className="flex flex-wrap gap-3 mt-4 text-xs"><button className="btn" onClick={()=>probe(p.id)} disabled={busy!==null}>{busy===p.id?'Checking…':'Check readiness'}</button><a className="underline text-cyan-300 self-center" href={p.official_docs} target="_blank" rel="noreferrer">Official API docs</a></div></article>})}</div>
 <p className="muted text-xs mt-4">A reachable public endpoint is not an authenticated account connection. No broker credentials have been stored and no real orders can be sent.</p></section>
}
