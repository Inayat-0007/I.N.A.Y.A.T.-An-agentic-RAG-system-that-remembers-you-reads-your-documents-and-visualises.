import React, { useState, useEffect } from 'react'
import LandingPage from './components/LandingPage.jsx'
import ArchitectureDiagram from './components/ArchitectureDiagram.jsx'
import FeaturesShowcase from './components/FeaturesShowcase.jsx'
import AgentWorkspace from './components/AgentWorkspace.jsx'
import ProductTour from './components/ProductTour.jsx'
import { Cpu, ShieldCheck, HelpCircle } from 'lucide-react'

export default function App() {
  const [activeView, setActiveView] = useState('landing') // 'landing' | 'agent'
  const [userId, setUserId] = useState('')
  const [showTour, setShowTour] = useState(false)
  const [apiOk, setApiOk] = useState(true)
  const [warnings, setWarnings] = useState([])

  // Parse URL query parameter for active user session on startup
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const userParam = params.get('user')
    
    // Check API availability first
    fetch('/api/startup')
      .then(res => res.json())
      .then(data => {
        setApiOk(data.ok)
        setWarnings(data.warnings || [])
        
        if (userParam && userParam.trim()) {
          setUserId(userParam.trim())
          setActiveView('agent')
        }
      })
      .catch(err => {
        console.error("Failed to query startup configurations:", err)
        // If connection fails, assume local development mock status or standard alert
      })
  }, [])

  // Sync active user to URL parameters
  const handleUserSessionChange = (newId) => {
    setUserId(newId)
    const url = new URL(window.location.href)
    if (newId && newId.trim()) {
      url.searchParams.set('user', newId.trim())
      window.history.pushState({}, '', url)
      setActiveView('agent')
    } else {
      url.searchParams.delete('user')
      window.history.pushState({}, '', url)
      setActiveView('landing')
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-cyber-bg font-body select-none">
      
      {/* 2026 Sleek Navbar */}
      <nav className="fixed top-0 left-0 w-full z-40 glass border-b border-cyber-border py-4 px-8 flex justify-between items-center">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveView('landing')}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyber-cyan to-cyber-magenta flex items-center justify-center shadow-lg shadow-cyber-cyan/25 animate-pulse-fast">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-heading font-black text-xl tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan to-cyber-magenta">
              I.N.A.Y.A.T.
            </span>
            <span className="hidden md:inline-block ml-3 px-2 py-0.5 text-[10px] font-heading font-semibold border border-cyber-cyan/30 bg-cyber-cyan/10 text-cyber-cyan rounded-md uppercase">
              Agentic RAG v2026
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <button 
            onClick={() => {
              const el = document.getElementById('architecture-section');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
              else setActiveView('landing');
            }} 
            className="text-sm font-subheading text-cyber-muted hover:text-white transition-colors duration-200"
          >
            System Architecture
          </button>
          
          <button 
            onClick={() => {
              const el = document.getElementById('features-section');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
              else setActiveView('landing');
            }}
            className="text-sm font-subheading text-cyber-muted hover:text-white transition-colors duration-200"
          >
            Engine Features
          </button>

          <button 
            onClick={() => setShowTour(true)}
            className="p-1.5 rounded-lg border border-cyber-border hover:border-cyber-cyan text-cyber-muted hover:text-cyber-cyan transition-colors"
            title="Start Interactive Tour"
          >
            <HelpCircle className="w-4 h-4" />
          </button>

          {activeView === 'landing' ? (
            <button
              onClick={() => {
                if (userId) setActiveView('agent');
                else {
                  // Prompt input on workspace or redirect
                  const inputEl = document.getElementById('landing-user-input');
                  if (inputEl) inputEl.focus();
                }
              }}
              className="px-5 py-2 rounded-xl text-sm font-heading font-bold text-white bg-gradient-to-r from-cyber-cyan to-cyber-magenta hover:shadow-lg hover:shadow-cyber-cyan/35 transition-all duration-300"
            >
              Launch Agent
            </button>
          ) : (
            <button
              onClick={() => handleUserSessionChange('')}
              className="px-5 py-2 rounded-xl text-sm font-heading font-bold text-cyber-muted hover:text-white border border-cyber-border hover:border-cyber-magenta transition-all duration-300"
            >
              Exit Workspace
            </button>
          )}
        </div>
      </nav>

      {/* Critical Startup Validation Block */}
      {!apiOk && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-filter backdrop-blur-md">
          <div className="max-w-md w-full p-8 rounded-2xl glass-glow-magenta text-center">
            <ShieldCheck className="w-16 h-16 text-cyber-magenta mx-auto mb-4 animate-bounce" />
            <h2 className="text-2xl font-heading font-bold mb-3 text-white">Critical Setup Error</h2>
            <p className="text-cyber-muted text-sm leading-relaxed mb-6">
              Duplicate your <code className="bg-white/10 px-1.5 py-0.5 rounded text-cyber-magenta">.env.example</code> file to <code className="bg-white/10 px-1.5 py-0.5 rounded text-cyber-magenta">.env</code> and populate your API credentials, then restart the application server.
            </p>
            {warnings.map((w, idx) => (
              <div key={idx} className="bg-red-500/10 border border-red-500/30 text-red-400 p-2.5 rounded-lg text-xs text-left mb-2">
                ⚠️ {w}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Page Routing */}
      {activeView === 'landing' ? (
        <div className="pt-20">
          <LandingPage onEnterWorkspace={handleUserSessionChange} />
          
          <div id="architecture-section">
            <ArchitectureDiagram />
          </div>

          <div id="features-section">
            <FeaturesShowcase />
          </div>
        </div>
      ) : (
        <div className="pt-[77px] h-[calc(100vh)]">
          <AgentWorkspace 
            userId={userId} 
            setUserId={handleUserSessionChange} 
          />
        </div>
      )}

      {/* Interactive SaaS Guided Tour Overlay */}
      {showTour && <ProductTour onClose={() => setShowTour(false)} />}
    </div>
  )
}
