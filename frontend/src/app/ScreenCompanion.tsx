'use client';
import {useEffect,useRef,useState} from 'react';

const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
type Analysis={instrument:string;timeframe:string;action:'BUY'|'SELL'|'WAIT';confidence:number;entry_zone:string;stop_loss:string;take_profit:string;reasoning:string;risk_warnings:string[];data_quality:string};
export default function ScreenCompanion(){
 const [sharing,setSharing]=useState(false),[busy,setBusy]=useState(false),[auto,setAuto]=useState(false),[intervalSec,setIntervalSec]=useState('8'),[status,setStatus]=useState('Screen sharing is off'),[analysis,setAnalysis]=useState<Analysis|null>(null),[error,setError]=useState('');
 const videoRef=useRef<HTMLVideoElement>(null),streamRef=useRef<MediaStream|null>(null),timerRef=useRef<ReturnType<typeof setInterval>|null>(null),busyRef=useRef(false);
 async function analyseFrame(){
  if(busyRef.current||!videoRef.current||!videoRef.current.videoWidth)return;
  busyRef.current=true;setBusy(true);setError('');
  try{
   const video=videoRef.current,canvas=document.createElement('canvas');const scale=Math.min(1,1440/video.videoWidth);
   canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);
   const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Could not read the shared screen');
   ctx.drawImage(video,0,0,canvas.width,canvas.height);
   const image=canvas.toDataURL('image/jpeg',0.78);
   const response=await fetch(API+'/api/visual-analysis',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_data_url:image,observed_at:new Date().toISOString()})});
   const data=await response.json();if(!response.ok)throw new Error(data.detail||'Visual analysis failed');
   setAnalysis(data.analysis);setStatus('Last chart review: '+new Date().toLocaleTimeString());
  }catch(e){setError(e instanceof Error?e.message:'Analysis failed');}
  finally{busyRef.current=false;setBusy(false);}
 }
 async function start(){
  try{
   setError('');
   const stream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:5},audio:false});
   streamRef.current=stream;
   if(videoRef.current){videoRef.current.srcObject=stream;await videoRef.current.play();}
   stream.getVideoTracks()[0].addEventListener('ended',stop);
   setSharing(true);setStatus('Screen is being shared · analysis is manual until enabled');
  }catch(e){setError(e instanceof Error?e.message:'Screen sharing was cancelled');}
 }
 function stop(){
  if(timerRef.current){clearInterval(timerRef.current);timerRef.current=null;}
  streamRef.current?.getTracks().forEach(t=>t.stop());streamRef.current=null;
  if(videoRef.current)videoRef.current.srcObject=null;
  setSharing(false);setAuto(false);setStatus('Screen sharing stopped');
 }
 useEffect(()=>()=>{if(timerRef.current)clearInterval(timerRef.current);streamRef.current?.getTracks().forEach(t=>t.stop());},[]);
 useEffect(()=>{if(sharing&&auto){timerRef.current=setInterval(()=>{void analyseFrame()},Math.max(5,Number(intervalSec)||8)*1000);}else if(timerRef.current){clearInterval(timerRef.current);timerRef.current=null;}return()=>{if(timerRef.current){clearInterval(timerRef.current);timerRef.current=null;}}},[sharing,auto,intervalSec]);
 return <section className="panel p-4 mt-5">
  <div className="flex flex-wrap justify-between gap-3 items-center"><div><div className="text-xs tracking-widest text-cyan-300 font-bold">LIVE SCREEN COMPANION</div><h2 className="text-xl font-bold mt-1">Analyse the platform you already use</h2><p className="muted text-sm mt-1">Share MetaTrader, a broker website or another chart window. You control when sharing starts and stops.</p></div><span className={'text-xs rounded-full px-3 py-1 '+(sharing?'bg-emerald-950 text-emerald-300':'bg-slate-800 text-slate-300')}>{sharing?'SCREEN SHARING ON':'NOT SHARING'}</span></div>
  <video ref={videoRef} muted playsInline className="w-full max-h-72 object-contain rounded-xl bg-slate-950 mt-4" />
  <div className="flex flex-wrap gap-2 mt-3">{!sharing?<button className="btn" onClick={start}>Share a screen or window</button>:<><button className="btn" onClick={()=>void analyseFrame()} disabled={busy}>{busy?'Analysing…':'Analyse this chart now'}</button><button className="btn border-rose-700 text-rose-300" onClick={stop}>Stop sharing</button></>}</div>
  {sharing&&<div className="mt-3 flex flex-wrap items-center gap-3 text-sm"><label className="flex items-center gap-2"><input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/>Review automatically</label><label className="flex items-center gap-2 muted">Every <select className="bg-slate-950 border border-slate-700 rounded p-1" value={intervalSec} onChange={e=>setIntervalSec(e.target.value)}><option value="8">8 sec</option><option value="15">15 sec</option><option value="30">30 sec</option><option value="60">60 sec</option></select></label></div>}
  <p className="muted text-xs mt-3">{status}. Screen images are sent to the configured AI service for analysis; avoid sharing passwords, payment details or other private information.</p>
  {error&&<p className="text-sm text-rose-300 mt-2">{error}</p>}
  {analysis&&<div className="mt-4 rounded-xl bg-slate-950 border border-slate-800 p-4"><div className="flex flex-wrap justify-between gap-2"><div><div className="muted text-xs">VISUAL CHART ASSESSMENT · {analysis.data_quality}</div><div className="text-3xl font-black mt-1">{analysis.action}</div></div><div className="text-right"><div className="muted text-xs">AI confidence estimate</div><div className="text-xl font-bold">{analysis.confidence}%</div></div></div><p className="text-sm mt-3">{analysis.instrument} · {analysis.timeframe}</p><div className="grid sm:grid-cols-3 gap-2 mt-3 text-sm">{[['Entry area',analysis.entry_zone],['Stop-loss idea',analysis.stop_loss],['Target idea',analysis.take_profit]].map(([k,v])=><div className="bg-slate-900 rounded-lg p-3" key={k}><div className="muted text-xs">{k}</div><b>{v}</b></div>)}</div><p className="text-sm mt-3 whitespace-pre-wrap">{analysis.reasoning}</p>{analysis.risk_warnings?.length>0&&<ul className="list-disc pl-5 mt-3 text-sm text-amber-200">{analysis.risk_warnings.map((w,i)=><li key={i}>{w}</li>)}</ul>}<p className="muted text-xs mt-3">Screenshot-based interpretation can misread prices, indicators or chart context. Verify every level on your broker platform. This is not a trade order or financial advice.</p></div>}
 </section>;
}
