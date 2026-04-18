import React, { useState, useEffect } from 'react'
import useSWR from 'swr'
import { 
  Activity, 
  Cpu, 
  Wallet, 
  TrendingUp, 
  Shield, 
  Gamepad2, 
  Bell,
  Settings,
  Circle,
  Power,
  X,
  Save
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

const SettingsModal = ({ isOpen, onClose }) => {
  const { data: envData, mutate } = useSWR(isOpen ? 'http://localhost:5000/api/env' : null, fetcher)
  const [formData, setFormData] = useState({})
  
  useEffect(() => {
    if (envData) setFormData(envData)
  }, [envData])

  const handleSave = async () => {
    try {
      await postFetcher('http://localhost:5000/api/env', formData)
      alert('Ambiente salvato! Il bot è stato riavviato con i nuovi parametri.')
      onClose()
    } catch (e) {
      alert('Errore salvataggio.')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-dark border border-white/10 p-6 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold flex items-center">
            <Settings className="mr-2 text-neon" /> .ENV Configuration
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-4">
          {!envData ? <p>Caricamento chiavi...</p> : Object.entries(formData).map(([k, v]) => (
            <div key={k}>
              <label className="block text-xs font-mono text-zinc-400 mb-1">{k}</label>
              <input 
                type={k.includes('KEY') || k.includes('SECRET') || k.includes('PASS') ? 'password' : 'text'}
                value={v}
                onChange={e => setFormData({...formData, [k]: e.target.value})}
                className="w-full bg-black/40 border border-white/10 rounded p-2 text-sm text-white font-mono focus:border-neon focus:outline-none"
              />
            </div>
          ))}
          <div className="pt-4 border-t border-white/10">
            <p className="text-xs text-yellow-500 mb-2">
              <Shield size={12} className="inline mr-1" />
              Aggiungi nuove chiavi specificando Nome e Valore:
            </p>
            <div className="flex space-x-2">
              <input id="newKey" placeholder="KEY_NAME" className="flex-1 bg-black/40 border border-white/10 rounded p-2 text-sm text-white font-mono" />
              <input id="newVal" placeholder="Value" className="flex-1 bg-black/40 border border-white/10 rounded p-2 text-sm text-white font-mono" />
              <button 
                onClick={() => {
                  const k = document.getElementById('newKey').value;
                  const val = document.getElementById('newVal').value;
                  if(k) setFormData({...formData, [k]: val});
                }}
                className="px-4 bg-white/10 hover:bg-white/20 rounded text-sm font-bold"
              >Add</button>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-white/10 flex justify-end">
          <button onClick={handleSave} className="bg-neon text-black px-6 py-2 rounded-lg font-bold flex items-center hover:bg-neon/80 transition-colors">
            <Save size={16} className="mr-2" /> Salva e Applica
          </button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const { data: state, error } = useSWR('http://localhost:5000/api/state', fetcher, { refreshInterval: 5000 })
  const { data: botStatus, mutate: mutateStatus } = useSWR('http://localhost:5000/api/bot/status', fetcher, { refreshInterval: 2000 })
  const [settingsOpen, setSettingsOpen] = useState(false)

  const toggleBot = async () => {
    const res = await postFetcher('http://localhost:5000/api/bot/toggle', {})
    mutateStatus({ ...botStatus, desired: res.desired })
  }

  if (!state || !botStatus) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin text-neon">
        <Activity size={48} />
      </div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-center mb-12 gap-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tighter text-gradient mb-1">NITRO<span className="text-white">BOT</span> V2</h1>
          <p className="text-zinc-500 text-sm flex items-center">
             <Shield size={14} className="mr-1 text-neon" /> AI-Powered Live Betting Engine
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <button 
            onClick={toggleBot}
            className={`px-4 py-2 flex items-center space-x-2 rounded-lg text-xs font-bold transition-all shadow-lg ${
              botStatus.running 
                ? 'bg-green-500/20 text-green-400 border border-green-500/50 hover:bg-green-500/30' 
                : 'bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30'
            }`}
          >
            <Power size={16} />
            <span>{botStatus.running ? 'PROCESS ONLINE' : 'PROCESS OFFLINE'}</span>
          </button>

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
          
          <button onClick={() => setSettingsOpen(true)} className="glass p-2 text-zinc-400 hover:text-white transition-colors">
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
              <span className="text-[10px] text-zinc-500">Real-time</span>
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
      
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
