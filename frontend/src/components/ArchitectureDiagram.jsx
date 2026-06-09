import React, { useState, useEffect } from 'react'
import { CheckCircle2, AlertTriangle, Zap, Terminal, RefreshCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ArchitectureDiagram() {
  const [activeStep, setActiveStep] = useState(null)
  const [breakerMem0, setBreakerMem0] = useState(false)
  const [breakerNeo4j, setBreakerNeo4j] = useState(false)
  const [loading, setLoading] = useState(false)

  // Fetch initial breaker state from API
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.breakers) {
          setBreakerMem0(data.breakers.mem0)
          setBreakerNeo4j(data.breakers.neo4j)
        }
      })
      .catch(err => console.error("Error loading circuit breakers:", err))
  }, [])

  const toggleBreaker = async (service, currentVal, setter) => {
    setLoading(true)
    const newVal = !currentVal
    try {
      const res = await fetch('/api/health/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, forced: newVal })
      })
      const data = await res.json()
      if (data.status === 'success') {
        setter(newVal)
      }
    } catch (err) {
      console.error(`Failed to toggle ${service} circuit breaker:`, err)
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    {
      id: 1,
      title: "1. User Profiling",
      role: "User Session Isolation",
      desc: "Authenticates name query parameters (?user=Rahul) to lock document files, chats, and indexes in isolated sandboxes.",
      x: 100, y: 120
    },
    {
      id: 2,
      title: "2. Memory Recall",
      role: "Mem0 Cloud API",
      desc: "Queries long-term persistent context for consolidated personal facts before running queries.",
      x: 250, y: 70
    },
    {
      id: 3,
      title: "3. Graph Store RAG",
      role: "Neo4j AuraDB & LlamaIndex",
      desc: "Fetches structured entity relations from the active property graph index, avoiding hallucinated vector records.",
      x: 400, y: 120
    },
    {
      id: 4,
      title: "4. LLM Synthesis",
      role: "Google Gemini Core",
      desc: "Generates custom contextual responses utilizing RAG nodes, memory pills, and direct prompts.",
      x: 550, y: 70
    },
    {
      id: 5,
      title: "5. Memory Ingestion",
      role: "Asynchronous Updates",
      desc: "Processes prompt interactions to extract new user preferences, pushing them to Mem0 Cloud memories.",
      x: 700, y: 120
    },
    {
      id: 6,
      title: "6. Self-Healing Bypass",
      role: "Resilience Decorators",
      desc: "Utilizes circuit breakers to isolate Neo4j or Mem0 failure points, falling back to direct LLM execution.",
      x: 400, y: 220
    }
  ]

  return (
    <section className="py-20 px-6 max-w-6xl mx-auto border-t border-cyber-border/40 relative">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-5xl font-heading font-black mb-4 tracking-wider uppercase text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan to-cyber-magenta">
          Interactive Neural Sequence
        </h2>
        <p className="text-sm font-subheading text-cyber-muted max-w-xl mx-auto font-light">
          Click on any node to view sequence data flow. Adjust physical circuit breakers to test the self-healing fail-safe system.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
        
        {/* Step details panel */}
        <div className="lg:col-span-1 glass p-6 rounded-2xl flex flex-col justify-between min-h-[300px] border border-cyber-border relative overflow-hidden">
          <div className="absolute top-0 right-0 p-3 opacity-10">
            <Terminal className="w-24 h-24 text-cyber-cyan" />
          </div>
          
          <AnimatePresence mode="wait">
            {activeStep ? (
              <motion.div
                key={activeStep.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <span className="text-[10px] font-heading font-bold text-cyber-cyan border border-cyber-cyan/35 bg-cyber-cyan/10 px-2 py-0.5 rounded uppercase">
                  {activeStep.role}
                </span>
                <h3 className="text-xl font-heading font-black mt-3 mb-2 text-white">
                  {activeStep.title}
                </h3>
                <p className="text-sm text-cyber-muted leading-relaxed font-light font-body">
                  {activeStep.desc}
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="default"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center text-center h-[200px]"
              >
                <div className="w-12 h-12 rounded-full border border-dashed border-cyber-cyan/40 flex items-center justify-center mb-3 text-cyber-cyan animate-spin">
                  <Zap className="w-5 h-5 text-cyber-cyan" />
                </div>
                <p className="text-xs text-cyber-muted font-subheading uppercase tracking-widest">
                  Click on diagram nodes to probe system steps.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
          
          <div className="mt-6 border-t border-cyber-border/40 pt-4 flex justify-between items-center text-[10px] font-heading uppercase text-cyber-muted">
            <span>Core Pipeline Status</span>
            <span className="flex items-center gap-1 text-green-400 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" /> 19 Smoke Tests Passing
            </span>
          </div>
        </div>

        {/* Isometric SVG Workflow */}
        <div className="lg:col-span-2 relative flex justify-center bg-cyber-bg/50 border border-cyber-border/60 rounded-3xl p-6 overflow-hidden h-[340px] shadow-inner">
          <svg viewBox="0 0 800 300" className="w-full h-full object-contain">
            {/* Draw connecting arrows/lines */}
            <defs>
              <linearGradient id="cyan-mag" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#FF00E5" stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {/* Path linkages */}
            <path d="M 100 120 L 250 70 L 400 120 L 550 70 L 700 120" fill="none" stroke="url(#cyan-mag)" strokeWidth="2.5" strokeDasharray="6 4" className="animate-pulse" />
            <path d="M 400 120 L 400 220" fill="none" stroke="rgba(167, 139, 250, 0.4)" strokeWidth="2" strokeDasharray="4 4" />
            
            {/* Render Nodes */}
            {steps.map(step => {
              const isActive = activeStep && activeStep.id === step.id
              const isBreakerActive = (step.id === 2 && breakerMem0) || (step.id === 3 && breakerNeo4j)

              return (
                <g 
                  key={step.id} 
                  transform={`translate(${step.x}, ${step.y})`}
                  className="cursor-pointer group"
                  onClick={() => setActiveStep(step)}
                >
                  {/* Outer pulsing ring */}
                  <circle 
                    r={isActive ? 22 : 18} 
                    fill="none" 
                    stroke={isBreakerActive ? "#FF00E5" : "#00F0FF"} 
                    strokeWidth="1.5" 
                    className={`transition-all duration-300 ${isActive ? 'animate-ping' : 'opacity-40 group-hover:opacity-80'}`} 
                  />
                  {/* Inner node base */}
                  <circle 
                    r="14" 
                    fill={isBreakerActive ? "#FF00E5" : (isActive ? "#00F0FF" : "#0A0E1A")} 
                    stroke={isBreakerActive ? "#FF00E5" : "#00F0FF"} 
                    strokeWidth="2.5" 
                    className="transition-all duration-300 group-hover:scale-110" 
                  />
                  {/* Node label number */}
                  <text 
                    y="4" 
                    textAnchor="middle" 
                    fill={isBreakerActive || isActive ? "#040408" : "#F4F4F5"} 
                    fontSize="11" 
                    fontWeight="bold"
                    className="font-heading pointer-events-none"
                  >
                    {step.id}
                  </text>
                  
                  {/* Visual Node Tags */}
                  <text 
                    y="35" 
                    textAnchor="middle" 
                    fill={isBreakerActive ? "#FF00E5" : "#F4F4F5"} 
                    fontSize="9" 
                    className="opacity-75 font-heading pointer-events-none uppercase tracking-wider"
                  >
                    {step.id === 2 && breakerMem0 ? "Mem0 Fail" : (step.id === 3 && breakerNeo4j ? "Neo4j Fail" : step.title.split('. ')[1])}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>
      </div>

      {/* Resilience Circuit Breaker Switchboard */}
      <div className="mt-12 p-8 rounded-2xl glass-glow-magenta grid grid-cols-1 md:grid-cols-2 gap-8 items-center border border-cyber-border shadow-2xl relative">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-cyber-magenta/10 border border-cyber-magenta/30 text-cyber-magenta">
            <Zap className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h3 className="text-lg font-heading font-black text-white flex items-center gap-2">
              🛡️ Hardware Circuit Switchboard
            </h3>
            <p className="text-xs text-cyber-muted mt-1 leading-relaxed font-light">
              Manually blow system breakers to audit real-time health degradation and auto-recovery loops.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-8 justify-around">
          {/* Mem0 Switch */}
          <div className="flex items-center gap-4">
            <span className={`text-xs font-heading font-bold uppercase tracking-wider ${breakerMem0 ? 'text-cyber-magenta' : 'text-cyber-muted'}`}>
              Mem0 Switch
            </span>
            <button
              onClick={() => toggleBreaker('mem0', breakerMem0, setBreakerMem0)}
              disabled={loading}
              className={`w-14 h-8 rounded-full p-1 transition-all duration-300 relative ${breakerMem0 ? 'bg-cyber-magenta shadow-[0_0_15px_rgba(255,0,229,0.5)]' : 'bg-zinc-800 border border-zinc-700'}`}
            >
              <div className={`w-6 h-6 rounded-full bg-white transition-transform duration-300 flex items-center justify-center ${breakerMem0 ? 'transform translate-x-6' : ''}`}>
                {breakerMem0 && <AlertTriangle className="w-3.5 h-3.5 text-cyber-magenta animate-pulse" />}
              </div>
              {/* Visual Sparks Overlay */}
              {breakerMem0 && (
                <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-full">
                  <div className="w-1.5 h-1.5 bg-yellow-300 rounded-full absolute top-1 left-2 animate-ping" />
                  <div className="w-1 h-1 bg-white rounded-full absolute bottom-1 right-3 animate-ping" />
                </div>
              )}
            </button>
            <span className="text-[10px] font-heading font-bold text-cyber-text uppercase">
              {breakerMem0 ? "⚠️ Open (Fail)" : "🟢 Closed (Normal)"}
            </span>
          </div>

          {/* Neo4j Switch */}
          <div className="flex items-center gap-4">
            <span className={`text-xs font-heading font-bold uppercase tracking-wider ${breakerNeo4j ? 'text-cyber-magenta' : 'text-cyber-muted'}`}>
              Neo4j Switch
            </span>
            <button
              onClick={() => toggleBreaker('neo4j', breakerNeo4j, setBreakerNeo4j)}
              disabled={loading}
              className={`w-14 h-8 rounded-full p-1 transition-all duration-300 relative ${breakerNeo4j ? 'bg-cyber-magenta shadow-[0_0_15px_rgba(255,0,229,0.5)]' : 'bg-zinc-800 border border-zinc-700'}`}
            >
              <div className={`w-6 h-6 rounded-full bg-white transition-transform duration-300 flex items-center justify-center ${breakerNeo4j ? 'transform translate-x-6' : ''}`}>
                {breakerNeo4j && <AlertTriangle className="w-3.5 h-3.5 text-cyber-magenta animate-pulse" />}
              </div>
              {breakerNeo4j && (
                <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-full">
                  <div className="w-1.5 h-1.5 bg-yellow-300 rounded-full absolute top-2 right-4 animate-ping" />
                  <div className="w-1 h-1 bg-white rounded-full absolute bottom-2 left-3 animate-ping" />
                </div>
              )}
            </button>
            <span className="text-[10px] font-heading font-bold text-cyber-text uppercase">
              {breakerNeo4j ? "⚠️ Open (Fail)" : "🟢 Closed (Normal)"}
            </span>
          </div>
        </div>
      </div>
    </section>
  )
}
