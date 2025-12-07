import { Link, useLocation } from 'react-router-dom'
import { Home, Send, Clock, FolderOpen, MessageSquare, Zap, Wifi, WifiOff } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function Header() {
  const location = useLocation()
  const [isConnected, setIsConnected] = useState(true)

  const isActive = (path) => location.pathname === path

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status')
        setIsConnected(response.ok)
      } catch (error) {
        setIsConnected(false)
      }
    }
    
    checkConnection()
    const interval = setInterval(checkConnection, 30000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="fileferry-gradient shadow-lg animate-fade-in">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg">
              <Zap className="text-yellow-300 w-7 h-7 animate-pulse-glow" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">FileFerry</h1>
              <p className="text-xs text-white/80">AI-Powered Transfer Agent</p>
            </div>
          </div>

          <nav className="flex space-x-1">
            <NavLink to="/dashboard" icon={Home} label="Dashboard" active={isActive('/dashboard')} />
            <NavLink to="/transfer" icon={Send} label="New Transfer" active={isActive('/transfer')} />
            <NavLink to="/history" icon={Clock} label="History" active={isActive('/history')} />
            <NavLink to="/explorer" icon={FolderOpen} label="Explorer" active={isActive('/explorer')} />
            <NavLink to="/chat" icon={MessageSquare} label="AI Chat" active={isActive('/chat')} />
          </nav>

          <div className="flex items-center space-x-2">
            {isConnected ? (
              <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/30">
                <Wifi className="w-4 h-4 text-green-300" />
                <span className="text-xs font-semibold text-white">Live</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 bg-red-500/30 backdrop-blur-sm px-3 py-1.5 rounded-full border border-red-400/50">
                <WifiOff className="w-4 h-4 text-red-200" />
                <span className="text-xs font-semibold text-white">Offline</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

function NavLink({ to, icon: Icon, label, active }) {
  return (
    <Link
      to={to}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
        active
          ? 'bg-white/25 backdrop-blur-sm text-white shadow-lg'
          : 'text-white/80 hover:bg-white/15 hover:text-white'
      }`}
    >
      <Icon size={18} />
      <span className="text-sm font-semibold">{label}</span>
    </Link>
  )
}
