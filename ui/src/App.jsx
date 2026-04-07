import React, { useState, useEffect } from 'react'
import useSWR from 'swr'
import { 
  Activity, 
  Cpu, 
  Wallet, 
  TrendingUp, 
  Shield, 
  Gamepad2, 
  LayoutDashboard,
  Bell,
  Settings,
  Circle
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const fetcher = (url) => fetch(url).then((res) => res.json())

const StatCard = ({ icon: Icon, title, value, color }) => (
  <div className="glass p-6 flex items-center space-x-4">
    <div className={`p-3 rounded-xl bg-${color}/10 text-${color}`}>
      <Icon size={24} />
    </div>
    <div>
      <p className="text-sm text-zinc-400">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  </div>
)

const MatchCard = ({ game }) => (
  <motion.div 
    layout
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass-dark p-1 overflow-hidden"
  >
    <div className="p-4 bg-white/5 border-b border-white/5 flex justify-between items-center">
      <span className="text-xs font-medium uppercase tracking-wider text-neon flex items-center">
        <Circle className="fill-neon mr-2" size={8} /> {game.sport}
      </span>
      <span className="text-xs text-zinc-500">{game.league}</span>
    </div>
    <div className="p-5">
      <h3 className="text-lg font-semibold text-center mb-4">{game.title}</h3>
      <div className="grid grid-cols-3 gap-2">
        {game.outcomes.map((o) => (
          <div key={o.outcomeId} className="bg-white/5 p-3 rounded-lg text-center border border-white/5 hover:border-neon/30 transition-colors">
            <p className="text-[10px] text-zinc-500 truncate mb-1">{o.name}</p>
            <p className="text-sm font-bold text-neon">{o.odds.toFixed(2)}</p>
          </div>
        ))}
      </div>
      {game.score && (
        <div className="mt-4 text-center">
          <span className="px-3 py-1 bg-accent/20 text-accent text-xs font-bold rounded-full">
            LIVE SCORE: {game.score}
          </span>
        </div>
      )}
    </div>
  </motion.div>
)

const AILogItem = ({ log }) => (
  <div className="flex items-start space-x-3 p-3 border-l-2 border-neon/50 bg-white/5 rounded-r-lg mb-2">
    <div className="mt-1">
      <Cpu size={16} className="text-neon" />
    </div>
    <div className="flex-1">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-bold text-zinc-300">{log.match}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${log.decision === 'Bet' ? 'bg-green-500/20 text-green-400' : 'bg-zinc-500/20 text-zinc-400'}`}>
          {log.decision}
        </span>
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed italic">"{log.recommendation}"</p>
      <div className="mt-2 flex items-center justify-between">
        <div className="h-1 flex-1 bg-zinc-800 rounded-full overflow-hidden mr-4">
          <div className="h-full bg-neon shadow-neon" style={{ width: `${log.confidence * 100}%` }}></div>
        </div>
        <span className="text-[10px] font-bold text-neon">{(log.confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  </div>
)

export default function App() {
  const { data: state, error } = useSWR('http://localhost:5000/api/state', fetcher, {
    refreshInterval: 5000
  })

  if (!state) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin text-neon">
        <Activity size={48} />
      </div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tighter text-gradient mb-1">NITRO<span className="text-white">BOT</span> V2</h1>
          <p className="text-zinc-500 text-sm flex items-center">
             <Shield size={14} className="mr-1 text-neon" /> AI-Powered Live Betting Engine
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => {
              if(window.confirm("Vuoi vendere tutte le posizioni e recuperare il saldo?")) {
                fetch('http://localhost:5000/api/liquidate', { method: 'POST' })
                  .then(r => r.json())
                  .then(data => alert(data.message));
              }
            }}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-lg shadow-red-500/20 flex items-center"
          >
            <Shield size={16} className="mr-2" /> RECOVER ALL FUNDS
          </button>
          <div className="glass px-4 py-2 flex items-center space-x-3">
            <div className="w-2 h-2 bg-neon rounded-full animate-pulse shadow-neon" />
            <span className="text-xs font-bold tracking-widest text-zinc-300 uppercase">Live Polygon</span>
          </div>
          <button className="glass p-2 text-zinc-400 hover:text-white transition-colors">
            <Settings size={20} />
          </button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <StatCard icon={Wallet} title="Balance USDC.e" value={`$${state.wallet.usdc.toFixed(2)}`} color="indigo-500" />
        <StatCard icon={Activity} title="Gas Balance" value={`${state.wallet.pol.toFixed(4)} POL`} color="neon" />
        <StatCard icon={TrendingUp} title="Active Bets" value={state.stats.total_bets} color="accent" />
        <StatCard icon={Gamepad2} title="Markets Live" value={state.live_games.length} color="green-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Feed */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Positions */}
          <div className="mb-12">
            <h2 className="text-xl font-bold flex items-center mb-6">
              <TrendingUp size={24} className="mr-2 text-accent" /> Active Positions
            </h2>
            <div className="glass-dark overflow-hidden rounded-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-white/5 text-xs font-medium text-zinc-400">
                    <tr>
                      <th className="px-6 py-4">Match</th>
                      <th className="px-6 py-4">Side</th>
                      <th className="px-6 py-4">Size</th>
                      <th className="px-6 py-4">Value</th>
                      <th className="px-6 py-4">PNL</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {state.active_bets && state.active_bets.length > 0 ? (
                      state.active_bets.map((bet, i) => (
                        <tr key={i} className="hover:bg-white/5 transition-colors">
                          <td className="px-6 py-4 text-sm font-medium">{bet.title}</td>
                          <td className="px-6 py-4 text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-bold ${bet.side === 'YES' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                              {bet.side}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-zinc-300">{bet.size.toFixed(2)}</td>
                          <td className="px-6 py-4 text-sm text-zinc-300">${bet.value.toFixed(2)}</td>
                          <td className={`px-6 py-4 text-sm font-bold ${bet.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {bet.pnl >= 0 ? '+' : ''}{bet.pnl.toFixed(2)}$
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="px-6 py-8 text-center text-zinc-500 text-sm">Nessuna posizione aperta</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Trade History */}
          <div className="mt-12">
            <h2 className="text-xl font-bold flex items-center mb-6 text-zinc-400">
              <Activity size={24} className="mr-2 text-indigo-400" /> Recent Activity
            </h2>
            <div className="glass-dark overflow-hidden rounded-xl border border-white/5">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-white/5 text-[10px] uppercase tracking-wider text-zinc-500">
                    <tr>
                      <th className="px-6 py-3">ID</th>
                      <th className="px-6 py-3">Asset</th>
                      <th className="px-6 py-3">Side</th>
                      <th className="px-6 py-3">Size</th>
                      <th className="px-6 py-3">Price</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {state.trade_history && state.trade_history.length > 0 ? (
                      state.trade_history.map((t, i) => (
                        <tr key={i} className="text-xs hover:bg-white/5 transition-colors">
                          <td className="px-6 py-3 font-mono text-zinc-500">#{t.id}</td>
                          <td className="px-6 py-3 font-medium">{t.asset}</td>
                          <td className="px-6 py-3">
                            <span className={`font-bold ${t.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                              {t.side}
                            </span>
                          </td>
                          <td className="px-6 py-3 text-zinc-400">{t.size.toFixed(2)}</td>
                          <td className="px-6 py-3 text-zinc-400">${t.price.toFixed(3)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="px-6 py-8 text-center text-zinc-600 italic">Nessuna attività recente</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {/* AI Logs */}
          <div className="glass p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold flex items-center">
                <Cpu size={20} className="mr-2 text-accent" /> AI Insights
              </h2>
              <span className="text-[10px] text-zinc-500">Real-time analysis</span>
            </div>
            
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              {state.ai_logs.length > 0 ? (
                state.ai_logs.map((log, i) => (
                  <AILogItem key={i} log={log} />
                ))
              ) : (
                <div className="text-center py-8 text-zinc-600 text-sm italic">
                  Analisi in corso...
                </div>
              )}
            </div>
          </div>

          {/* Wallet Address */}
          <div className="glass p-6 overflow-hidden">
            <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-4">Connected Wallet</h2>
            <p className="text-xs font-mono text-neon break-all bg-neon/5 p-3 rounded-lg border border-neon/10">
              {state.wallet.address}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
