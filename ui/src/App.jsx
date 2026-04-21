import React, { useState, useEffect } from 'react'
import useSWR from 'swr'
import { 
  Activity, 
  Cpu, 
  Wallet, 
  TrendingUp, 
  Shield, 
  Gamepad2, 
  Settings,
  Power,
  X,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  BarChart3,
  RefreshCw,
  Terminal
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const fetcher = (url) => fetch(url).then((res) => res.json())
const postFetcher = async (url, data) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)

const StatCard = ({ icon: Icon, title, value, subValue, color, delay = 0 }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="glass p-5 flex flex-col justify-between border-l-4"
    style={{ borderLeftColor: `var(--color-${color})` }}
  >
    <div className="flex justify-between items-start mb-4">
      <div className={`p-2 rounded-lg bg-white/5 text-${color}`}>
        <Icon size={20} />
      </div>
      {subValue && <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">{subValue}</span>}
    </div>
    <div>
      <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">{title}</p>
      <p className="text-2xl font-black tracking-tight">{value}</p>
    </div>
  </motion.div>
)

const TradeRow = ({ trade }) => {
  const isWin = trade.result === 'WIN'
  const isLoss = trade.result === 'LOSS'
  
  return (
    <motion.tr 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="hover:bg-white/5 transition-colors border-b border-white/5"
    >
      <td className="px-5 py-3">
        <div className="flex flex-col">
          <span className="text-xs font-bold">{trade.market.split('-')[0]}</span>
          <span className="text-[10px] text-zinc-500">{new Date(trade.ts * 1000).toLocaleTimeString()}</span>
        </div>
      </td>
      <td className="px-5 py-3">
        <div className={`flex items-center text-[10px] font-bold ${trade.side === 'UP' ? 'text-neon' : 'text-accent'}`}>
          {trade.side === 'UP' ? <ArrowUpRight size={12} className="mr-1" /> : <ArrowDownRight size={12} className="mr-1" />}
          {trade.side}
        </div>
      </td>
      <td className="px-5 py-3">
        <span className="text-xs font-mono text-zinc-300">{(trade.entry_price * 100).toFixed(0)}¢</span>
      </td>
      <td className="px-5 py-3">
        {trade.result ? (
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-black ${isWin ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-100'}`}>
            {trade.result}
          </span>
        ) : (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-black bg-zinc-500/20 text-zinc-400">PENDING</span>
        )}
      </td>
      <td className="px-5 py-3 text-right">
        <span className={`text-xs font-bold ${isWin ? 'text-green-400' : isLoss ? 'text-red-400' : 'text-zinc-500'}`}>
          {isWin ? '+1.00 USDC' : isLoss ? '-1.10 USDC' : '--'}
        </span>
      </td>
    </motion.tr>
  )
}

const LivePrediction = ({ market, btcPrice }) => {
  if (!market) return null
  
  const progress = Math.min((Date.now()/1000 - market.start_timestamp) / (market.end_timestamp - market.start_timestamp), 1)
  const remaining = Math.max(0, Math.round(market.end_timestamp - Date.now()/1000))
  
  return (
    <div className="glass-dark p-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 h-1 bg-neon/30 w-full">
        <motion.div 
          className="h-full bg-neon shadow-neon"
          initial={{ width: 0 }}
          animate={{ width: `${progress * 100}%` }}
        />
      </div>
      
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-2">
          <Clock size={16} className="text-zinc-500" />
          <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">{remaining}s REMAINING</span>
        </div>
        <div className="px-3 py-1 bg-neon/10 border border-neon/20 rounded-full">
          <span className="text-[10px] font-black text-neon uppercase">BTC/USDC PAIR</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8 mb-6">
        <div>
          <p className="text-[10px] font-bold text-zinc-500 uppercase mb-1">Target Price</p>
          <p className="text-2xl font-black tracking-tighter">${market.anchor_price?.toLocaleString() || '---'}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-zinc-500 uppercase mb-1">Current Price</p>
          <p className="text-2xl font-black tracking-tighter text-neon animate-pulse">${btcPrice?.toLocaleString()}</p>
        </div>
      </div>

      <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
        <div className="flex items-center">
          <div className="mr-4 p-2 bg-neon/20 rounded-lg text-neon">
            <Target size={20} />
          </div>
          <div>
            <p className="text-xs font-bold">{market.title}</p>
            <p className="text-[10px] text-zinc-500">Vol: ${market.volume?.toFixed(0)}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-zinc-500 uppercase">Strategy</p>
          <p className="text-xs font-black text-accent uppercase">SMART SNIPER v2</p>
        </div>
      </div>
    </div>
  )
}

const LogEvent = ({ logLine, idx }) => {
  let icon = <Activity size={12} />
  let color = "text-zinc-400"
  let bg = "bg-white/5"
  let message = logLine

  if (logLine.includes('NUOVA FINESTRA')) {
    icon = <Gamepad2 size={12} />; color = "text-neon"; bg = "bg-neon/10";
    message = logLine.split('—')[1] || logLine;
  } else if (logLine.includes('🎯 BET') || logLine.includes('🔫 Invio ordine')) {
    icon = <Target size={12} />; color = "text-accent"; bg = "bg-accent/10";
  } else if (logLine.includes('✅') || logLine.includes('WIN')) {
    icon = <TrendingUp size={12} />; color = "text-green-400"; bg = "bg-green-500/10";
  } else if (logLine.includes('❌') || logLine.includes('LOSS')) {
    icon = <X size={12} />; color = "text-red-400"; bg = "bg-red-500/10";
  } else if (logLine.includes('💰 Riscatto')) {
    icon = <Wallet size={12} />; color = "text-indigo-400"; bg = "bg-indigo-500/10";
  } else if (logLine.includes('⚓ Price to Beat')) {
    icon = <Shield size={12} />; color = "text-zinc-300";
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: idx * 0.05 }}
      className={`flex items-center p-3 rounded-xl ${bg} border border-white/5 mb-2`}
    >
      <div className={`p-1.5 rounded-lg ${color} mr-3 bg-black/20`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-[10px] font-bold ${color} truncate`}>{message}</p>
      </div>
    </motion.div>
  )
}

export default function App() {
  const { data: state, mutate: mutateState } = useSWR('/api/state', fetcher, { refreshInterval: 2000 })
  const { data: botStatus, mutate: mutateStatus } = useSWR('/api/bot/status', fetcher, { refreshInterval: 2000 })
  const { data: systemLogs } = useSWR('/api/logs', fetcher, { refreshInterval: 2000 })
  
  const [isRefreshing, setIsRefreshing] = useState(false)

  const toggleBot = async () => {
    const res = await postFetcher('/api/bot/toggle', {})
    mutateStatus({ ...botStatus, desired: res.desired })
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await mutateState()
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  if (!state || !botStatus) return (
    <div className="min-h-screen bg-[#0a0a0c] flex items-center justify-center p-8">
      <div className="flex flex-col items-center">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
          <RefreshCw className="text-neon" size={48} />
        </motion.div>
        <p className="mt-4 text-xs font-black tracking-widest text-zinc-600 uppercase">Synchronizing Engine...</p>
      </div>
    </div>
  )

  const liveMarket = state.live_games?.length > 0 ? state.live_games[0] : null
  const btcPrice = state.live_games?.length > 0 ? state.live_games[0].current_price : null
  const stats = state.stats || { pnl: 0, win_rate: 0, wins: 0, losses: 0, volume: 0 }

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-zinc-100 font-sans selection:bg-neon selection:text-black">
      <div className="max-w-7xl mx-auto px-4 py-8 md:py-12">
        {/* Navbar */}
        <header className="flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-neon to-accent rounded-2xl flex items-center justify-center shadow-lg shadow-neon/20">
              <Cpu className="text-black" size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tighter flex items-center uppercase">
                NitroBot <span className="text-neon ml-2">V2.5</span>
              </h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${botStatus.running ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  {botStatus.running ? 'System Operational' : 'System Offline'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
             <button 
              onClick={handleRefresh}
              className={`p-2 glass text-zinc-400 hover:text-neon transition-colors ${isRefreshing ? 'animate-spin' : ''}`}
            >
              <RefreshCw size={20} />
            </button>
            <button 
              onClick={toggleBot}
              className={`px-6 py-2.5 rounded-xl text-xs font-black tracking-widest transition-all uppercase flex items-center ${
                botStatus.running 
                  ? 'bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20' 
                  : 'bg-green-500/10 text-green-500 border border-green-500/20 hover:bg-green-500/20'
              }`}
            >
              <Power size={16} className="mr-2" />
              {botStatus.running ? 'Stop Bot' : 'Start Bot'}
            </button>
            <div className="h-10 w-[1px] bg-white/10 mx-2" />
            <div className="flex flex-col items-end">
              <p className="text-[10px] font-bold text-zinc-500 uppercase">Gas Fee Reserve</p>
              <p className="text-sm font-black text-indigo-400">{state.wallet.pol.toFixed(3)} POL</p>
            </div>
          </div>
        </header>

        {/* Top Dash */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <StatCard 
            icon={Wallet} 
            title="Available Capital" 
            value={formatCurrency(state.wallet.usdc)} 
            subValue="USDC.e (Polygon)"
            color="indigo-500" 
            delay={0.1}
          />
          <StatCard 
            icon={BarChart3} 
            title="Total PNL" 
            value={formatCurrency(stats.pnl)} 
            subValue="Verified Profit"
            color={stats.pnl >= 0 ? "green-500" : "red-500"} 
            delay={0.2}
          />
          <StatCard 
            icon={Target} 
            title="Win Rate" 
            value={`${stats.win_rate}%`} 
            subValue={`${stats.wins} Wins / ${stats.losses} Losses`}
            color="neon" 
            delay={0.3}
          />
          <StatCard 
            icon={TrendingUp} 
            title="Total Volume" 
            value={formatCurrency(stats.volume)} 
            subValue="CLOB Activity"
            color="accent" 
            delay={0.4}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Predictions & Infographic Logs */}
          <div className="lg:col-span-8 space-y-8">
            <section tabIndex="0">
              <h2 className="text-lg font-black uppercase tracking-tighter mb-4 flex items-center">
                <Activity size={20} className="mr-2 text-neon" /> Live Market Tracking
              </h2>
              <LivePrediction market={liveMarket} btcPrice={btcPrice} />
            </section>

            <section tabIndex="0" className="mt-8">
              <h2 className="text-lg font-black uppercase tracking-tighter mb-4 flex items-center">
                <Terminal size={20} className="mr-2 text-zinc-400" /> Live Event Feed
              </h2>
              <div className="glass-dark p-6 rounded-2xl border border-white/5 h-[400px] overflow-y-auto custom-scrollbar bg-black/40">
                {systemLogs?.logs && systemLogs.logs.length > 0 ? (
                  <div className="flex flex-col-reverse">
                    {systemLogs.logs.slice(-50).map((logLine, idx) => (
                      <LogEvent key={idx} logLine={logLine} idx={idx} />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-zinc-600 italic">
                    <Activity size={32} className="mb-4 opacity-20" />
                    <p className="text-sm">Waiting for system events...</p>
                  </div>
                )}
              </div>
            </section>
          </div>

          {/* Right Column: Trade History */}
          <div className="lg:col-span-4 flex flex-col h-full">
            <h2 className="text-lg font-black uppercase tracking-tighter mb-4 flex items-center">
              <Clock size={20} className="mr-2 text-accent" /> Recent Trades (Max 20)
            </h2>
            <div className="glass-dark flex-1 overflow-hidden flex flex-col rounded-3xl border border-white/5 bg-black/20">
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                <table className="w-full text-left">
                  <thead className="sticky top-0 bg-[#0a0a0c] text-[10px] font-black text-zinc-500 uppercase tracking-widest border-b border-white/5">
                    <tr>
                      <th className="px-5 py-4 font-black">Market</th>
                      <th className="px-5 py-4 font-black text-center">Side</th>
                      <th className="px-5 py-4 text-right">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {state.recent_trades && state.recent_trades.length > 0 ? (
                      state.recent_trades.map((t, i) => (
                        <tr key={i} className="hover:bg-white/5 transition-colors">
                          <td className="px-5 py-4 italic text-xs font-medium text-zinc-300">
                             {t.market.split(' ')[0]} {t.market.split(' ').slice(-1)}
                          </td>
                          <td className="px-5 py-4 text-center">
                             <span className={`text-[10px] font-bold ${t.side === 'UP' ? 'text-neon' : 'text-accent'}`}>{t.side}</span>
                          </td>
                          <td className="px-5 py-4 text-right">
                             <span className={`text-[10px] font-black px-2 py-1 rounded-full ${t.result === 'WIN' ? 'bg-green-500/10 text-green-400' : t.result === 'LOSS' ? 'bg-red-500/10 text-red-400' : 'bg-white/5 text-zinc-500'}`}>
                                {t.result || 'PENDING'}
                             </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="3" className="px-5 py-12 text-center text-zinc-600 italic text-sm">
                          No recent trades found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="p-5 bg-white/5 border-t border-white/5 text-center">
                <p className="text-[10px] font-black text-neon uppercase tracking-[0.2em] animate-pulse">Live Dashboard Active</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
