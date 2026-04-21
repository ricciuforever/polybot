<?php
/**
 * POLYBOT PREMIUM DASHBOARD v3 (PHP Edition)
 * Designed for High-Frequency Trading Monitoring
 */

error_reporting(E_ALL);
ini_set('display_errors', 0);
session_start();

// --- CONFIGURAZIONE SICUREZZA ---
$env_file = __DIR__ . '/.env';
$config = [];
if (file_exists($env_file)) {
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $config[trim($name)] = trim($value, ' "');
    }
}

$auth_user = $config['AUTH_USERNAME'] ?? 'admin';
$auth_pass = $config['AUTH_PASSWORD'] ?? 'polybot2024';

// Logout
if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: index.php");
    exit;
}

// Login Check
if (isset($_POST['login'])) {
    if ($_POST['user'] === $auth_user && $_POST['pass'] === $auth_pass) {
        $_SESSION['logged_in'] = true;
    } else {
        $error = "Credenziali non valide";
    }
}

if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true):
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | Polybot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: radial-gradient(circle at top left, #0f172a, #000); height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Inter', sans-serif; color: white; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
    </style>
</head>
<body>
    <div class="glass p-8 w-full max-w-md shadow-2xl">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">POLYBOT v3</h1>
            <p class="text-slate-400 mt-2">Accedi al terminale di trading</p>
        </div>
        <form method="POST" class="space-y-6">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Username</label>
                <input type="text" name="user" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
                <input type="password" name="pass" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
            </div>
            <?php if(isset($error)): ?>
                <p class="text-red-400 text-sm bg-red-400/10 p-2 rounded"><?php echo $error; ?></p>
            <?php endif; ?>
            <button type="submit" name="login" class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-3 rounded-lg transition-all transform hover:scale-[1.02]">
                ACCEDI
            </button>
        </form>
    </div>
</body>
</html>
<?php exit; endif; ?>

<?php
// API Handler per refresh dinamico
if (isset($_GET['api'])) {
    header('Content-Type: application/json');
    $state = file_exists('bot_state.json') ? json_decode(file_get_contents('bot_state.json'), true) : [];
    $trades = file_exists('trades_history.json') ? json_decode(file_get_contents('trades_history.json'), true) : [];
    
    // Leggi ultime 50 righe di log
    $logs = [];
    if (file_exists('dashboard_log.txt')) {
        $log_content = file('dashboard_log.txt');
        $logs = array_slice($log_content, -50);
        $logs = array_map('trim', $logs);
    }

    echo json_encode(['state' => $state, 'trades' => $trades, 'logs' => $logs]);
    exit;
}
?>

<!DOCTYPE html>
<html lang="it" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Polybot Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body { background-color: #020617; color: #f8fafc; font-family: 'Outfit', sans-serif; }
        .glass-card { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glow-green { box-shadow: 0 0 15px rgba(34, 197, 94, 0.1); }
        .glow-red { box-shadow: 0 0 15px rgba(239, 68, 68, 0.1); }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    </style>
</head>
<body class="p-4 md:p-8">

    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- HEADER -->
        <header class="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 rounded-3xl">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
                    <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </div>
                <div>
                    <h1 class="text-2xl font-bold tracking-tight">Polybot <span class="text-indigo-400">Pro</span></h1>
                    <p class="text-sm text-slate-400 mono" id="wallet-address">Connessione in corso...</p>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <div class="text-right hidden md:block">
                    <p class="text-xs text-slate-500 uppercase tracking-widest font-bold">Stato Motore</p>
                    <div class="flex items-center justify-end gap-2 text-emerald-400 font-bold" id="status-badge">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        LIVE
                    </div>
                </div>
                <a href="index.php?logout=1" class="p-3 bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded-xl transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                </a>
            </div>
        </header>

        <!-- STATS GRID -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="glass-card p-6 rounded-3xl relative overflow-hidden group">
                <div class="relative z-10">
                    <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Saldo USDC</p>
                    <h2 class="text-3xl font-bold mono" id="stat-usdc">$0.00</h2>
                </div>
                <div class="absolute -right-4 -bottom-4 text-slate-800 opacity-20 group-hover:opacity-40 transition-opacity">
                    <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.82v-1.91c-1.57-.22-2.79-.88-3.66-1.98.85-.56 1.81-.88 2.82-.88.24 0 .48.02.71.06 1.13.21 1.95.82 2.46 1.83l.49-.03zM12 15c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"/></svg>
                </div>
            </div>

            <div class="glass-card p-6 rounded-3xl">
                <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Win Rate</p>
                <h2 class="text-3xl font-bold mono text-emerald-400" id="stat-wr">0%</h2>
                <p class="text-xs text-slate-500 mt-2" id="stat-total-trades">0 trades completati</p>
            </div>

            <div class="glass-card p-6 rounded-3xl">
                <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">PNL Totale</p>
                <h2 class="text-3xl font-bold mono" id="stat-pnl">$0.00</h2>
                <div class="h-1 bg-slate-800 rounded-full mt-3 overflow-hidden">
                    <div class="h-full bg-indigo-500 w-1/2"></div>
                </div>
            </div>

            <div class="glass-card p-6 rounded-3xl">
                <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Saldo POL</p>
                <h2 class="text-3xl font-bold mono text-purple-400" id="stat-pol">0.00</h2>
                <p class="text-xs text-slate-500 mt-2">Gas per transazioni</p>
            </div>
        </div>

        <!-- MAIN LAYOUT: ACTIVE MARKETS & LOGS -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- LIVE MARKETS -->
            <div class="lg:col-span-2 space-y-6">
                <div class="glass-card rounded-3xl overflow-hidden">
                    <div class="p-6 border-b border-white/5 flex items-center justify-between">
                        <h3 class="font-bold text-lg flex items-center gap-2">
                            <span class="w-2 h-2 bg-indigo-500 rounded-full"></span>
                            Mercati Attivi (Live)
                        </h3>
                        <span class="text-xs mono text-slate-500 uppercase">Aggiornato ora</span>
                    </div>
                    <div class="p-2 overflow-x-auto">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-slate-500 text-xs uppercase mono">
                                    <th class="p-4">Asset / Titolo</th>
                                    <th class="p-4 text-center">PTB</th>
                                    <th class="p-4 text-center">Attuale</th>
                                    <th class="p-4 text-right">Distanza %</th>
                                </tr>
                            </thead>
                            <tbody id="market-list" class="divide-y divide-white/5">
                                <!-- JS Populates this -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- RECENT TRADES -->
                <div class="glass-card rounded-3xl overflow-hidden">
                    <div class="p-6 border-b border-white/5">
                        <h3 class="font-bold text-lg">Storico Operazioni Recenti</h3>
                    </div>
                    <div class="p-2 overflow-x-auto">
                        <table class="w-full">
                            <thead>
                                <tr class="text-slate-500 text-xs uppercase mono text-left">
                                    <th class="p-4">Time</th>
                                    <th class="p-4">Mercato</th>
                                    <th class="p-4">Side</th>
                                    <th class="p-4">Entry</th>
                                    <th class="p-4">Esito</th>
                                </tr>
                            </thead>
                            <tbody id="trade-list" class="divide-y divide-white/5">
                                <!-- JS Populates this -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- LOGS & SIDEBAR -->
            <div class="space-y-6">
                <div class="glass-card rounded-3xl flex flex-col h-[600px]">
                    <div class="p-6 border-b border-white/5 flex items-center justify-between">
                        <h3 class="font-bold flex items-center gap-2 text-indigo-400">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"></path></svg>
                            Live Engine Logs
                        </h3>
                        <div class="flex items-center gap-1">
                           <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></div>
                           <span class="text-[10px] text-slate-500 mono">STREAM</span>
                        </div>
                    </div>
                    <div id="log-view" class="p-4 flex-1 overflow-y-auto mono text-[11px] leading-relaxed text-slate-300">
                        <!-- Logs here -->
                    </div>
                </div>

                <div class="glass-card p-6 rounded-3xl">
                    <h4 class="text-sm font-bold uppercase text-slate-500 mb-4">Link Rapidi</h4>
                    <div class="space-y-3">
                        <a href="https://polymarket.com" target="_blank" class="flex items-center justify-between p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20 transition-all font-semibold">
                            Polymarket Explorer
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                        </a>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('index.php?api=1');
                const data = await response.json();
                
                // Aggiorna Wallet & Stats
                const state = data.state;
                if (state.wallet) {
                    document.getElementById('wallet-address').innerText = state.wallet.address.substring(0, 10) + '...' + state.wallet.address.substring(34);
                    document.getElementById('stat-usdc').innerText = '$' + parseFloat(state.wallet.usdc).toFixed(2);
                    document.getElementById('stat-pol').innerText = parseFloat(state.wallet.pol).toFixed(4);
                }
                
                if (state.stats) {
                    document.getElementById('stat-wr').innerText = (state.stats.win_rate || 0) + '%';
                    document.getElementById('stat-total-trades').innerText = (state.stats.total || 0) + ' trades completati';
                    document.getElementById('stat-pnl').innerText = '$' + (state.stats.pnl || 0).toFixed(2);
                    document.getElementById('stat-pnl').className = 'text-3xl font-bold mono ' + (state.stats.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
                }

                // Aggiorna Mercati
                const marketList = document.getElementById('market-list');
                marketList.innerHTML = '';
                if (state.live_games && state.live_games.length > 0) {
                    state.live_games.forEach(m => {
                        const distance = ((m.current_price - m.anchor_price) / m.anchor_price) * 100;
                        const color = distance >= 0 ? 'text-emerald-400' : 'text-rose-400';
                        marketList.innerHTML += `
                            <tr class="hover:bg-white/5 transition-colors group">
                                <td class="p-4">
                                    <div class="font-bold text-slate-200">${m.title}</div>
                                    <div class="text-[10px] text-slate-500 uppercase mono">ID: ${m.id}</div>
                                </td>
                                <td class="p-4 text-center mono text-slate-400">$${m.anchor_price.toLocaleString()}</td>
                                <td class="p-4 text-center mono text-white">$${m.current_price.toLocaleString()}</td>
                                <td class="p-4 text-right mono font-bold ${color}">${distance > 0 ? '+' : ''}${distance.toFixed(3)}%</td>
                            </tr>
                        `;
                    });
                } else {
                    marketList.innerHTML = '<tr><td colspan="4" class="p-8 text-center text-slate-500 italic">Nessun mercato attivo al momento</td></tr>';
                }

                // Aggiorna Trade Recenti
                const tradeList = document.getElementById('trade-list');
                const recentTrades = state.recent_trades || [];
                tradeList.innerHTML = '';
                recentTrades.slice(0, 10).forEach(t => {
                    const statusClass = t.result === 'WIN' ? 'bg-emerald-500/20 text-emerald-400' : (t.result === 'LOSS' ? 'bg-rose-500/20 text-rose-400' : 'bg-indigo-500/20 text-indigo-400');
                    const time = new Date(t.ts * 1000).toLocaleTimeString();
                    tradeList.innerHTML += `
                        <tr class="text-sm border-white/5">
                            <td class="p-4 mono text-slate-500">${time}</td>
                            <td class="p-4 font-bold text-slate-300 overflow-hidden text-ellipsis whitespace-nowrap max-w-[200px]">${t.market}</td>
                            <td class="p-4"><span class="px-2 py-1 rounded text-[10px] font-bold ${t.side === 'UP' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}">${t.side}</span></td>
                            <td class="p-4 mono text-slate-400">${Math.round(t.entry_price * 100)}¢</td>
                            <td class="p-4">
                                <span class="px-3 py-1 rounded-full text-[10px] font-bold ${statusClass}">${t.result || 'PENDING'}</span>
                            </td>
                        </tr>
                    `;
                });

                // Aggiorna Logs
                const logView = document.getElementById('log-view');
                const scrollDown = logView.scrollHeight - logView.scrollTop <= logView.clientHeight + 20;
                logView.innerHTML = data.logs.map(log => {
                    let colorClass = 'text-slate-400';
                    if (log.includes('✅') || log.includes('SUCCESS')) colorClass = 'text-emerald-400';
                    if (log.includes('❌') || log.includes('ERROR')) colorClass = 'text-rose-400 font-bold';
                    if (log.includes('⚠️') || log.includes('WARNING')) colorClass = 'text-amber-400';
                    if (log.includes('🎯') || log.includes('BET')) colorClass = 'text-indigo-400 font-bold';
                    return `<div class="${colorClass} mb-1">${log}</div>`;
                }).join('');
                if (scrollDown) logView.scrollTop = logView.scrollHeight;

            } catch (err) {
                console.error("Dashboard Update Error:", err);
            }
        }

        setInterval(updateDashboard, 5000);
        updateDashboard();
    </script>
</body>
</html>
