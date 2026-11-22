'use client';
import {useEffect,useRef,useState} from 'react';
import {CandlestickSeries,ColorType,HistogramSeries,createChart,type IChartApi,type UTCTimestamp} from 'lightweight-charts';

type Candle={time:number;open:number;high:number;low:number;close:number;volume:number};
type CandleResponse={symbol:string;timeframe:string;source:string;mode:string;candles:Candle[]};
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
const frames=['5m','15m','1h','4h','1d'];
export default function MarketChart({symbol}:{symbol:string}){
 const host=useRef<HTMLDivElement|null>(null);
 const chart=useRef<IChartApi|null>(null);
 const [timeframe,setTimeframe]=useState('1h');
 const [candles,setCandles]=useState<Candle[]>([]);
 const [source,setSource]=useState('—');
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 useEffect(()=>{
  if(!host.current)return;
  const instance=createChart(host.current,{
   width:host.current.clientWidth,height:360,
   layout:{background:{type:ColorType.Solid,color:'#0b1322'},textColor:'#9aabc4'},
   grid:{vertLines:{color:'#17243a'},horzLines:{color:'#17243a'}},
   rightPriceScale:{borderColor:'#26364d'},
   timeScale:{borderColor:'#26364d',timeVisible:true,secondsVisible:false},
   crosshair:{vertLine:{color:'#49627f'},horzLine:{color:'#49627f'}},
  });
  chart.current=instance;
  const candleSeries=instance.addSeries(CandlestickSeries,{
   upColor:'#20c997',downColor:'#ff647c',borderUpColor:'#20c997',borderDownColor:'#ff647c',
   wickUpColor:'#20c997',wickDownColor:'#ff647c',
  });
  const volumeSeries=instance.addSeries(HistogramSeries,{
   priceFormat:{type:'volume'},priceScaleId:'volume',
  });
  instance.priceScale('volume').applyOptions({scaleMargins:{top:0.82,bottom:0},visible:false});
  const resize=new ResizeObserver(entries=>{
   const width=entries[0]?.contentRect.width;
   if(width)instance.applyOptions({width});
  });
  resize.observe(host.current);
  (instance as IChartApi & {__candleSeries?:typeof candleSeries;__volumeSeries?:typeof volumeSeries}).__candleSeries=candleSeries;
  (instance as IChartApi & {__volumeSeries?:typeof volumeSeries}).__volumeSeries=volumeSeries;
  return()=>{resize.disconnect();instance.remove();chart.current=null};
 },[]);
 useEffect(()=>{
  let cancelled=false;
  async function load(){
   setLoading(true);setError('');
   try{
    const response=await fetch(API+'/api/candles?symbol='+encodeURIComponent(symbol)+'&timeframe='+timeframe+'&limit=150',{cache:'no-store'});
    if(!response.ok)throw new Error('Could not load chart data');
    const payload:CandleResponse=await response.json();
    if(cancelled)return;
    setCandles(payload.candles||[]);setSource(payload.source||'DEMO');
    const instance=chart.current as (IChartApi & {__candleSeries?:any;__volumeSeries?:any})|null;
    if(instance?.__candleSeries){
     instance.__candleSeries.setData(payload.candles.map(c=>({time:c.time as UTCTimestamp,open:c.open,high:c.high,low:c.low,close:c.close})));
     instance.__volumeSeries?.setData(payload.candles.map(c=>({time:c.time as UTCTimestamp,value:c.volume,color:c.close>=c.open?'rgba(32,201,151,.35)':'rgba(255,100,124,.35)'})));
     instance.timeScale().fitContent();
    }
   }catch(e){if(!cancelled)setError(e instanceof Error?e.message:'Chart unavailable')}
   finally{if(!cancelled)setLoading(false)}
  }
  load();
  const timer=window.setInterval(load,30000);
  return()=>{cancelled=true;window.clearInterval(timer)};
 },[symbol,timeframe]);
 const latest=candles[candles.length-1];
 return <section className="panel p-4 mb-5">
  <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
   <div><h2 className="font-bold text-lg">Advanced chart · {symbol}</h2><p className="muted text-xs">Candlesticks · volume · crosshair · auto-refresh 30s</p></div>
   <div className="flex gap-1 flex-wrap">{frames.map(frame=><button key={frame} onClick={()=>setTimeframe(frame)} className={'btn text-xs '+(timeframe===frame?'border-cyan-400 text-cyan-200':'')}>{frame}</button>)}</div>
  </div>
  <div className="flex items-center gap-3 text-xs mb-2"><span className={source==='BINANCE'?'text-emerald-300':'text-amber-300'}>● {source} {source==='BINANCE'?'LIVE':'DEMO DATA'}</span>{loading&&<span className="muted">Updating…</span>}{latest&&<span className="muted">Last close: {latest.close.toLocaleString(undefined,{maximumFractionDigits:6})}</span>}</div>
  <div ref={host} className="w-full" style={{height:360}}/>
  {error&&<p className="text-sm text-rose-300 mt-2">{error}</p>}
  <p className="muted text-xs mt-2">BTC/USD and ETH/USD use Binance candles when available. Other instruments and provider outages use clearly labelled illustrative candles.</p>
 </section>
}
