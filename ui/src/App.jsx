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
  RefreshCw
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
          <span className="text-[10px] font-black text-neon uppercase">{market.asset}/USDC PAIR</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8 mb-6">
        <div>
          <p className="text-[10px] font-bold text-zinc-500 uppercase mb-1">Target Price</p>
          <p className="text-2xl font-black tracking-tighter">${market.anchor_price?.toLocaleString() || '---'}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-zinc-500 uppercase mb-1">Current Price</p>
          <p className="text-2xl font-black tracking-tighter text-neon animate-pulse">${market.current_price?.toLocaleString()}</p>
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

export default function App() {
  const { data: state, mutate: mutateState } = useSWR('/api/state', fetcher, { refreshInterval: 2000 })
  const { data: stats } = useSWR('/api/stats', fetcher, { refreshInterval: 10000 })
  const { data: trades } = useSWR('/api/trades', fetcher, { refreshInterval: 10000 })
  const { data: botStatus, mutate: mutateStatus } = useSWR('/api/bot/status', fetcher, { refreshInterval: 2000 })
  
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

  const liveMarkets = state.live_games || []

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
                NitroBot <span className="text-neon ml-2">V2.1</span>
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
            value={formatCurrency((stats?.wins || 0) - (stats?.losses || 0) * 1.1)} 
            subValue="Verified Profit"
            color="green-500" 
            delay={0.2}
          />
          <StatCard 
            icon={Target} 
            title="Win Rate" 
            value={`${stats?.win_rate || 0}%`} 
            subValue={`${stats?.wins || 0} Wins / ${stats?.losses || 0} Losses`}
            color="neon" 
            delay={0.3}
          />
          <StatCard 
            icon={TrendingUp} 
            title="Total Volume" 
            value={formatCurrency((stats?.total || 0) * 1.1)} 
            subValue="CLOB Activity"
            color="accent" 
            delay={0.4}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Predictions & Stats */}
          <div className="lg:col-span-8 space-y-8">
            <section tabIndex="0">
              <h2 className="text-lg font-black uppercase tracking-tighter mb-4 flex items-center">
                <Activity size={20} className="mr-2 text-neon" /> Live Market Tracking
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {liveMarkets.map((m, i) => (
                  <LivePrediction key={m.id || i} market={m} />
                ))}
                {liveMarkets.length === 0 && (
                  <div className="glass-dark p-12 text-center text-zinc-600 italic">
                    Nessun mercato attivo rilevato.
                  </div>
                )}
              </div>
            </section>

            <section tabIndex="0">
              <div className="flex justify-between items-center mb-6">
                 <h2 className="text-lg font-black uppercase tracking-tighter flex items-center">
                  <BarChart3 size={20} className="mr-2 text-indigo-400" /> Performance Analysis
                </h2>
                <span className="text-[10px] font-bold text-zinc-500 uppercase">Last 24 Hours</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[1, 2, 3].map(i => (
                  <div key={i} className="glass p-4">
                    <div className="flex items-center justify-between mb-2">
                       <span className="text-[10px] font-bold text-zinc-500 uppercase">Asset {i === 1 ? 'BTC' : i === 2 ? 'ETH' : 'SOL'}</span>
                       <span className="text-[10px] font-black text-green-400">+12%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                       <motion.div initial={{ width: 0 }} animate={{ width: `${60+i*10}%` }} className="h-full bg-gradient-to-r from-neon to-indigo-500" />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Right Column: Trade History */}
          <div className="lg:col-span-4 flex flex-col h-full">
            <h2 className="text-lg font-black uppercase tracking-tighter mb-4 flex items-center">
              <Clock size={20} className="mr-2 text-accent" /> Trade History
            </h2>
            <div className="glass-dark flex-1 overflow-hidden flex flex-col">
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                <table className="w-full text-left">
                  <thead className="sticky top-0 bg-[#16161a] text-[10px] font-black text-zinc-500 uppercase tracking-widest border-b border-white/5">
                    <tr>
                      <th className="px-5 py-3">Market</th>
                      <th className="px-5 py-3">Side</th>
                      <th className="px-5 py-3">Price</th>
                      <th className="px-5 py-3">Result</th>
                      <th className="px-5 py-3 text-right">PNL</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {trades && trades.length > 0 ? (
                      trades.map((t, i) => (
                        <TradeRow key={i} trade={t} />
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="px-5 py-12 text-center text-zinc-600 italic text-sm">
                          No recent trades found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-white/5 border-t border-white/5 text-center">
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Connected: {state.wallet.address.substring(0,6)}...{state.wallet.address.substring(38)}</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
