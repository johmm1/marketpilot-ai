'use client';
import { FormEvent, useEffect, useState } from 'react';

const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
type User={id:string;email:string;created_at:string};

export default function AuthGate({children}:{children:React.ReactNode}){
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true);
 const [mode,setMode]=useState<'login'|'register'>('login');
 const [email,setEmail]=useState(''),[password,setPassword]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 async function checkSession(){
  try{const r=await fetch(API+'/api/auth/me',{credentials:'include',cache:'no-store'});if(r.ok)setUser(await r.json());else setUser(null)}
  catch{setError('Cannot reach the account service. Check your connection and try again.')}
  finally{setLoading(false)}
 }
 useEffect(()=>{checkSession()},[]);
 async function submit(event:FormEvent){
  event.preventDefault();setBusy(true);setError('');
  try{
   const r=await fetch(API+'/api/auth/'+(mode==='login'?'login':'register'),{
    method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email,password})
   });
   const d=await r.json();
   if(!r.ok)throw new Error(d.detail||'Account request failed');
   setUser(d);setPassword('');
  }catch(e){setError(e instanceof Error?e.message:'Account service unavailable')}
  finally{setBusy(false)}
 }
 async function signOut(){
  setBusy(true);
  try{await fetch(API+'/api/auth/logout',{method:'POST',credentials:'include'});setUser(null)}
  finally{setBusy(false)}
 }
 if(loading)return <main className="min-h-screen grid place-items-center p-6"><div className="panel p-6">Checking your secure session…</div></main>;
 if(!user)return <main className="min-h-screen grid place-items-center p-5">
  <section className="panel w-full max-w-md p-6 md:p-8">
   <div className="text-xs tracking-[.3em] text-cyan-300 font-bold">MARKET INTELLIGENCE</div>
   <h1 className="text-3xl font-black mt-2">MARKETPILOT <span className="text-cyan-300">AI</span></h1>
   <p className="muted text-sm mt-2">{mode==='login'?'Sign in to your private trading workspace.':'Create your private MarketPilot account.'}</p>
   <form onSubmit={submit} className="mt-6 space-y-3">
    <label className="block text-sm">Email address<input required type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full mt-1 rounded-lg border border-slate-700 bg-slate-950 p-3"/></label>
    <label className="block text-sm">Password<input required type="password" minLength={mode==='register'?12:1} maxLength={128} autoComplete={mode==='login'?'current-password':'new-password'} value={password} onChange={e=>setPassword(e.target.value)} className="w-full mt-1 rounded-lg border border-slate-700 bg-slate-950 p-3"/></label>
    {mode==='register'&&<p className="muted text-xs">Use at least 12 characters. Keep your password private.</p>}
    {error&&<p role="alert" className="text-rose-300 text-sm">{error}</p>}
    <button className="btn w-full" disabled={busy}>{busy?'Please wait…':mode==='login'?'Sign in':'Create account'}</button>
   </form>
   <button className="text-cyan-300 text-sm mt-4" onClick={()=>{setMode(mode==='login'?'register':'login');setError('')}}>
    {mode==='login'?'New to MarketPilot? Create an account':'Already registered? Sign in'}
   </button>
   <p className="muted text-xs mt-6">Market data and signals are educational. Trading is disabled; paper orders are simulated only.</p>
  </section>
 </main>;
 return <><div className="max-w-7xl mx-auto px-4 pt-3 flex justify-end items-center gap-3 text-xs muted"><span>{user.email}</span><button className="btn" disabled={busy} onClick={signOut}>Sign out</button></div>{children}</>;
}
