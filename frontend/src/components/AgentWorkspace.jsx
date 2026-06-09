import React, { useState, useEffect, useRef } from 'react'
import { 
  Send, User, Cpu, RefreshCw, Trash2, BookOpen, Upload, 
  CheckCircle, Database, ToggleLeft, ToggleRight, Sparkles,
  ChevronLeft, ChevronRight, Share2, HelpCircle, Brain
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { DataSet, Network } from 'vis-network/standalone/umd/vis-network.min.js'

export default function AgentWorkspace({ userId, setUserId }) {
  const [messages, setMessages] = useState([])
  const [inputVal, setInputVal] = useState('')
  const [loading, setLoading] = useState(false)
  const [indexing, setIndexing] = useState(false)
  const [memories, setMemories] = useState([])
  const [health, setHealth] = useState({ gemini: '⚪ Unknown', mem0: '⚪ Unknown', neo4j: '⚪ Unknown' })
  const [breakers, setBreakers] = useState({ mem0: false, neo4j: false })
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [graphOpen, setGraphOpen] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)

  const chatEndRef = useRef(null)
  const networkRef = useRef(null)
  const containerRef = useRef(null)

  // Load chat history & memories from local storage key / API on user switch
  useEffect(() => {
    if (!userId) return
    
    // Load chat history
    const cachedHistory = localStorage.getItem(`messages_${userId}`)
    if (cachedHistory) {
      setMessages(JSON.parse(cachedHistory))
    } else {
      setMessages([])
    }

    // Load memories
    refreshMemories()
    
    // Load health status
    refreshHealth()
  }, [userId])

  // Cache message changes to local storage
  useEffect(() => {
    if (userId) {
      localStorage.setItem(`messages_${userId}`, JSON.stringify(messages))
    }
  }, [messages, userId])

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Render network graph when graphOpen is toggled
  useEffect(() => {
    if (!graphOpen || !userId) return

    fetch(`/api/graph?user_id=${userId}`)
      .then(res => res.json())
      .then(graphData => {
        const container = containerRef.current
        if (!container) return

        const nodes = new DataSet(graphData.nodes)
        const edges = new DataSet(graphData.edges)

        const options = {
          nodes: {
            shape: 'dot',
            size: 20,
            font: { color: '#ffffff', size: 13, face: 'Outfit, sans-serif' },
            borderWidth: 2,
            shadow: true
          },
          edges: {
            width: 2,
            color: { color: 'rgba(129, 140, 248, 0.4)', highlight: '#c084fc' },
            font: { color: '#a5b4fc', size: 10, align: 'horizontal', background: '#040408' },
            arrows: { to: { enabled: true, scaleFactor: 0.7 } },
            smooth: { type: 'cubicBezier', forceDirection: 'none', roundness: 0.4 }
          },
          groups: {
            Agent: { color: { background: '#c084fc', border: '#a78bfa' } },
            LLM: { color: { background: '#34d399', border: '#059669' } },
            Memory: { color: { background: '#60a5fa', border: '#2563eb' } },
            GraphStore: { color: { background: '#fb7185', border: '#e11d48' } },
            Resilience: { color: { background: '#fbbf24', border: '#d97706' } },
            User: { color: { background: '#f472b6', border: '#db2777' } },
            Entity: { color: { background: '#818cf8', border: '#6366f1' } },
            Chunk: { color: { background: '#94a3b8', border: '#475569' } }
          },
          physics: {
            stabilization: false,
            barnesHut: { gravitationalConstant: -3500, springConstant: 0.04, springLength: 120 }
          },
          interaction: { hover: true }
        }

        const network = new Network(container, { nodes, edges }, options)
        networkRef.current = network

        // Event hooks
        network.on("selectNode", (params) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0]
            const node = nodes.get(nodeId)
            setSelectedNode(node)
            setSelectedEdge(null)
          }
        })

        network.on("selectEdge", (params) => {
          if (params.nodes.length === 0 && params.edges.length > 0) {
            const edgeId = params.edges[0]
            const edge = edges.get(edgeId)
            
            // Get node labels
            const fromNode = nodes.get(edge.from)
            const toNode = nodes.get(edge.to)
            
            setSelectedEdge({
              ...edge,
              fromLabel: fromNode ? fromNode.label : `Node ${edge.from}`,
              toLabel: toNode ? toNode.label : `Node ${edge.to}`
            })
            setSelectedNode(null)
          }
        })

        network.on("deselectNode", () => {
          setSelectedNode(null)
        })

        network.on("deselectEdge", () => {
          setSelectedEdge(null)
        })
      })
      .catch(err => console.error("Error drawing graph:", err))

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [graphOpen, userId])

  // API wrappers
  const refreshMemories = async () => {
    try {
      const res = await fetch(`/api/memories?user_id=${userId}`)
      const data = await res.json()
      setMemories(data.memories || [])
    } catch (err) {
      console.error("Error refreshing memory list:", err)
    }
  }

  const refreshHealth = async () => {
    try {
      const res = await fetch('/api/health')
      const data = await res.json()
      setHealth(data.statuses || {})
      setBreakers(data.breakers || {})
    } catch (err) {
      console.error("Error updating system health:", err)
    }
  }

  const toggleBreaker = async (service, currentVal) => {
    const newVal = !currentVal
    try {
      const res = await fetch('/api/health/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, forced: newVal })
      })
      const data = await res.json()
      if (data.status === 'success') {
        refreshHealth()
      }
    } catch (err) {
      console.error("Failed to toggle breaker state:", err)
    }
  }

  const clearUserMemory = async () => {
    if (!window.confirm("Are you sure you want to clear this user profile memories?")) return
    try {
      const res = await fetch(`/api/memories/clear?user_id=${userId}`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'success') {
        setMemories([])
      }
    } catch (err) {
      console.error("Failed to clear memory database:", err)
    }
  }

  const sendMessage = async (textToSend) => {
    const promptText = textToSend || inputVal
    if (!promptText.trim()) return

    if (!textToSend) setInputVal('')
    
    // Add user message
    const userMsg = { role: 'user', content: promptText }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const memoryCtx = memories.map(m => `• ${m}`).join('\n')
      
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: promptText,
          user_id: userId,
          memory_context: memoryCtx
        })
      })
      const data = await res.json()

      // Add assistant response
      const assistantMsg = { 
        role: 'assistant', 
        content: data.answer,
        // Detect citations based on returned context
        isRag: data.answer.toLowerCase().includes("embedding") || data.answer.toLowerCase().includes("document") || !data.answer.toLowerCase().includes("fallback"),
        isMemory: memories.some(m => data.answer.toLowerCase().includes(m.split(' ')[0].toLowerCase()))
      }
      
      setMessages(prev => [...prev, assistantMsg])
      
      // Update memory tags list
      if (data.memories) {
        setMemories(data.memories)
      } else {
        refreshMemories()
      }
      
      // Trigger graph data check if open
      if (graphOpen) {
        // Redraw Vis.js graph
        setGraphOpen(false)
        setTimeout(() => setGraphOpen(true), 50)
      }

    } catch (err) {
      console.error("Query execution failed:", err)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "API timeout. The backend server failed to respond in time." 
      }])
    } finally {
      setLoading(false)
    }
  }

  // File Upload Ingestion
  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIndexing(true)
    const formData = new FormData()
    formData.append('user_id', userId)
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.status === 'success') {
        alert(`Successfully ingested: ${data.indexed_files.join(', ')}. Graph Index updated!`)
        // Trigger graph redraw
        if (graphOpen) {
          setGraphOpen(false)
          setTimeout(() => setGraphOpen(true), 50)
        }
      } else {
        alert(data.detail || "Upload failed.")
      }
    } catch (err) {
      console.error("Ingestion failed:", err)
      alert("Failed to ingest files.")
    } finally {
      setIndexing(false)
    }
  }

  // Use graph node / edge inside chat
  const handleInjectPrompt = (promptText) => {
    setGraphOpen(false)
    sendMessage(promptText)
  }

  const renderStatus = (status) => {
    if (status.includes("Connected")) {
      return <span className="w-2.5 h-2.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.7)] animate-pulse" />
    } else if (status.includes("Fail") || status.includes("Unreachable")) {
      return <span className="w-2.5 h-2.5 rounded-full bg-cyber-magenta shadow-[0_0_8px_rgba(255,0,229,0.7)]" />
    } else {
      return <span className="w-2.5 h-2.5 rounded-full bg-zinc-600" />
    }
  }

  return (
    <div className="h-full flex relative select-text overflow-hidden">
      
      {/* Sidebar Trigger (Floating button) */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute top-4 left-4 z-30 p-2 rounded-xl glass border border-cyber-border hover:border-cyber-cyan text-cyber-muted hover:text-cyber-cyan transition-colors"
      >
        {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>

      {/* Sidebar Panel */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full flex-shrink-0 glass border-r border-cyber-border/80 flex flex-col z-20"
          >
            {/* Top Workspace Identity */}
            <div className="p-6 pt-16 border-b border-cyber-border/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-cyber-cyan/15 border border-cyber-cyan/35 flex items-center justify-center font-heading font-black text-cyber-cyan">
                  {userId ? userId.substring(0,2).toUpperCase() : 'U'}
                </div>
                <div>
                  <h4 className="text-xs font-heading font-bold text-cyber-muted uppercase tracking-widest">Active workspace</h4>
                  <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    className="bg-transparent border-none text-white text-base font-subheading font-bold focus:outline-none focus:ring-0 w-32 p-0"
                    placeholder="Workspace Name"
                  />
                </div>
              </div>

              {/* Memory Pills List */}
              <div className="mt-4">
                <h5 className="text-[10px] font-heading font-bold text-cyber-muted uppercase tracking-widest mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyber-cyan animate-pulse" /> Persistent Facts ({memories.length})
                </h5>
                <div className="max-h-24 overflow-y-auto flex flex-wrap gap-1.5 p-1 pr-2">
                  {memories.map((m, idx) => (
                    <span 
                      key={idx} 
                      className="px-2 py-0.5 rounded-full text-[10px] font-subheading bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan hover:border-cyber-cyan transition-colors"
                      title={m}
                    >
                      {m.length > 25 ? m.substring(0, 25) + '...' : m}
                    </span>
                  ))}
                  {memories.length === 0 && (
                    <span className="text-[10px] font-subheading text-cyber-muted italic">No facts extracted yet.</span>
                  )}
                </div>
              </div>
            </div>

            {/* Ingestion zone */}
            <div className="p-6 border-b border-cyber-border/50">
              <h5 className="text-[10px] font-heading font-bold text-cyber-muted uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-purple-400" /> Ingest Documents
              </h5>
              
              <label className="flex flex-col items-center justify-center border border-dashed border-cyber-border hover:border-cyber-cyan/50 rounded-xl p-4 bg-cyber-bg/30 cursor-pointer hover:bg-cyber-cyan/5 transition-all duration-300 relative overflow-hidden group">
                <input 
                  type="file" 
                  multiple 
                  accept=".pdf,.txt" 
                  onChange={handleFileUpload} 
                  className="hidden" 
                  disabled={indexing}
                />
                
                {indexing ? (
                  <div className="flex flex-col items-center py-2">
                    <RefreshCw className="w-8 h-8 text-cyber-cyan animate-spin mb-2" />
                    <span className="text-[10px] font-heading font-bold text-cyber-cyan uppercase tracking-wider animate-pulse">Indexing graph...</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center py-2 text-center">
                    <Upload className="w-6 h-6 text-cyber-muted group-hover:text-cyber-cyan group-hover:scale-110 transition-all duration-300 mb-2" />
                    <span className="text-[10px] font-subheading font-bold text-cyber-text">Upload PDF / TXT Files</span>
                    <span className="text-[9px] text-cyber-muted font-light mt-1">Saves to data/documents/</span>
                  </div>
                )}
              </label>
            </div>

            {/* Health indicators panel */}
            <div className="p-6 border-b border-cyber-border/50">
              <div className="flex justify-between items-center mb-3">
                <h5 className="text-[10px] font-heading font-bold text-cyber-muted uppercase tracking-widest flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-cyber-gold" /> System Health
                </h5>
                <button 
                  onClick={refreshHealth} 
                  className="p-1 rounded hover:bg-white/5 text-cyber-muted hover:text-white transition-colors"
                  title="Force Refresh Health"
                >
                  <RefreshCw className="w-3 h-3" />
                </button>
              </div>

              <div className="flex flex-col gap-2">
                {[
                  { key: 'gemini', label: 'Gemini LLM' },
                  { key: 'mem0', label: 'Mem0 Memory' },
                  { key: 'neo4j', label: 'Neo4j GraphDB' }
                ].map(svc => (
                  <div key={svc.key} className="flex justify-between items-center py-1.5 px-3 rounded-lg bg-white/[0.02] border border-cyber-border/40 text-xs">
                    <span className="text-cyber-muted font-subheading">{svc.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-medium font-body text-white">{health[svc.key]}</span>
                      {renderStatus(health[svc.key])}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Resilience Testing Checkboxes */}
            <div className="p-6 border-b border-cyber-border/50">
              <h5 className="text-[10px] font-heading font-bold text-cyber-muted uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <ToggleLeft className="w-3.5 h-3.5 text-cyber-magenta" /> Fault Tolerance Testing
              </h5>

              <div className="flex flex-col gap-2.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-cyber-muted">Simulate Mem0 Outage</span>
                  <button
                    onClick={() => toggleBreaker('mem0', breakers.mem0)}
                    className="text-cyber-muted hover:text-cyber-magenta transition-colors"
                  >
                    {breakers.mem0 ? <ToggleRight className="w-6 h-6 text-cyber-magenta" /> : <ToggleLeft className="w-6 h-6" />}
                  </button>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-cyber-muted">Simulate Neo4j Outage</span>
                  <button
                    onClick={() => toggleBreaker('neo4j', breakers.neo4j)}
                    className="text-cyber-muted hover:text-cyber-magenta transition-colors"
                  >
                    {breakers.neo4j ? <ToggleRight className="w-6 h-6 text-cyber-magenta" /> : <ToggleLeft className="w-6 h-6" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Actions Panel */}
            <div className="p-6 mt-auto flex gap-3">
              <button 
                onClick={clearUserMemory}
                className="flex-1 py-2 px-3 border border-cyber-border hover:border-cyber-magenta rounded-xl text-[10px] font-heading font-bold text-cyber-muted hover:text-cyber-magenta flex items-center justify-center gap-1.5 transition-all duration-200"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear Memory
              </button>
              <button 
                onClick={() => setMessages([])}
                className="flex-1 py-2 px-3 border border-cyber-border hover:border-cyber-cyan rounded-xl text-[10px] font-heading font-bold text-cyber-muted hover:text-cyber-cyan flex items-center justify-center gap-1.5 transition-all duration-200"
              >
                <RefreshCw className="w-3.5 h-3.5" /> New Chat
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full bg-cyber-bg relative z-10">
        
        {/* Top Header info */}
        <div className="py-4 px-6 border-b border-cyber-border flex justify-between items-center pl-16">
          <div>
            <h2 className="text-sm font-heading font-black text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyber-cyan animate-pulse" /> Inayat Workspace Chat
            </h2>
            <p className="text-[10px] font-subheading text-cyber-muted mt-0.5">
              Active workspace folder: <span className="text-white">data/documents/{userId}/</span>
            </p>
          </div>

          <button
            onClick={() => setGraphOpen(true)}
            className="flex items-center gap-2 px-4 py-2 border border-cyber-cyan/40 bg-cyber-cyan/10 text-cyber-cyan hover:bg-cyber-cyan hover:text-cyber-bg text-xs font-heading font-bold rounded-xl shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all duration-300"
          >
            <Share2 className="w-4 h-4 animate-spin-slow" /> Visualize Neural Graph
          </button>
        </div>

        {/* Message Panel Scroll Grid */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          
          {/* Welcome guide when history is empty */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto opacity-70">
              <div className="w-16 h-16 rounded-full bg-white/[0.02] border border-cyber-border/40 flex items-center justify-center mb-4 text-cyber-cyan">
                <Brain className="w-8 h-8 text-cyber-cyan animate-pulse" />
              </div>
              <h3 className="text-base font-heading font-bold mb-2 text-white">Agentic Workspace Initialized</h3>
              <p className="text-xs text-cyber-muted leading-relaxed font-light font-body">
                Upload your document database in the sidebar or ask questions about Rahul's ML NLP classes to trigger property graphs.
              </p>
            </div>
          )}

          {/* List messages */}
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className={`max-w-[75%] p-4 ${msg.role === 'user' ? 'chat-bubble-user text-white' : 'chat-bubble-ai text-cyber-text'}`}>
                
                {/* Role label header */}
                <div className="flex justify-between items-center text-[9px] font-heading font-extrabold uppercase tracking-widest mb-1.5">
                  <span className={msg.role === 'user' ? 'text-cyber-cyan' : 'text-green-400'}>
                    {msg.role === 'user' ? 'You' : 'I.N.A.Y.A.T.'}
                  </span>
                  
                  {/* Citations list tags */}
                  {msg.role === 'assistant' && (
                    <div className="flex gap-1">
                      {msg.isRag && <span className="bg-purple-500/20 text-purple-400 border border-purple-500/35 px-1 rounded">Graph RAG</span>}
                      {msg.isMemory && <span className="bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/35 px-1 rounded">Mem0 Context</span>}
                      {!msg.isRag && <span className="bg-cyber-magenta/20 text-cyber-magenta border border-cyber-magenta/35 px-1 rounded">LLM Fallback</span>}
                    </div>
                  )}
                </div>

                <p className="text-sm leading-relaxed font-light whitespace-pre-wrap">{msg.content}</p>
              </div>
            </motion.div>
          ))}

          {/* Spinner Thinking card */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 p-4 text-xs font-heading font-bold text-cyber-cyan animate-pulse"
            >
              <Cpu className="w-4 h-4 text-cyber-cyan animate-spin" /> Thinking and recalling database records...
            </motion.div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input prompt bar footer */}
        <div className="p-4 border-t border-cyber-border bg-cyber-bg/40">
          <form 
            onSubmit={(e) => {
              e.preventDefault()
              sendMessage()
            }}
            className="flex gap-3 max-w-4xl mx-auto items-center"
          >
            <input
              type="text"
              placeholder="Ask about your documents, or tell me about yourself..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-xl bg-cyber-bg border border-cyber-border text-white text-sm focus:outline-none focus:border-cyber-cyan focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all duration-300"
            />
            <button
              type="submit"
              disabled={loading}
              className="p-3 bg-gradient-to-r from-cyber-cyan to-cyber-magenta hover:scale-105 rounded-xl flex items-center justify-center text-cyber-bg font-bold shadow-lg shadow-cyber-cyan/25 transition-all duration-200"
            >
              <Send className="w-4 h-4 text-cyber-bg" />
            </button>
          </form>
        </div>
      </main>

      {/* Sliding Knowledge Graph Overlay Screen */}
      <AnimatePresence>
        {graphOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.35 }}
            className="absolute inset-0 z-40 flex bg-cyber-bg/95 backdrop-filter backdrop-blur-md"
          >
            {/* Graph Visualizer Panel */}
            <div className="flex-1 h-full relative">
              
              {/* Back CTA */}
              <button 
                onClick={() => setGraphOpen(false)}
                className="absolute top-4 left-4 z-50 px-4 py-2 bg-zinc-900 border border-cyber-border hover:border-cyber-cyan text-white text-xs font-heading rounded-xl shadow-lg transition-colors"
              >
                ← Back to Workspace Chat
              </button>

              <div className="absolute top-4 right-4 z-30 bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan px-3 py-1.5 rounded-xl text-xs font-heading font-bold flex items-center gap-1.5 animate-pulse">
                <Sparkles className="w-4 h-4" /> Interactive Vis.js Canvas
              </div>

              {/* Vis.js network container */}
              <div ref={containerRef} className="w-full h-full" />
            </div>

            {/* Properties details panel drawer */}
            <div className="w-80 h-full border-l border-cyber-border bg-cyber-bg/90 p-6 flex flex-col justify-between overflow-y-auto">
              <div>
                <h3 className="text-base font-heading font-black text-white border-b border-cyber-border pb-3 mb-6 flex items-center gap-2">
                  <Share2 className="w-5 h-5 text-cyber-cyan" /> Neural Details
                </h3>

                {selectedNode ? (
                  <div className="space-y-4">
                    <span className="text-[10px] font-heading font-bold bg-cyber-cyan/15 border border-cyber-cyan/35 text-cyber-cyan px-2 py-0.5 rounded uppercase">
                      Node Properties ({selectedNode.group})
                    </span>
                    <h4 className="text-lg font-heading font-bold text-white mt-2 leading-tight">
                      {selectedNode.label}
                    </h4>

                    <div className="bg-zinc-950/60 border border-cyber-border/40 rounded-xl p-4 mt-4 max-h-96 overflow-y-auto">
                      {selectedNode.properties && Object.keys(selectedNode.properties).map(key => (
                        <div key={key} className="mb-3">
                          <label className="text-[9px] font-heading font-bold text-cyber-muted uppercase tracking-wider block mb-0.5">{key}</label>
                          <span className="text-xs text-cyber-text block leading-relaxed whitespace-pre-wrap">{selectedNode.properties[key]}</span>
                        </div>
                      ))}
                    </div>

                    <button 
                      onClick={() => {
                        const label = selectedNode.label
                        const props = selectedNode.properties || {}
                        let promptText = `Tell me more about ${label}`
                        if (props.text) {
                          promptText = `From the document chunk details, tell me more about: ${props.text.substring(0, 150)}...`
                        } else if (props.Description) {
                          promptText = `Tell me about ${label}: ${props.Description}`
                        }
                        handleInjectPrompt(promptText)
                      }}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-magenta text-cyber-bg font-heading font-extrabold text-xs flex items-center justify-center gap-1.5 mt-6 shadow-lg shadow-cyber-cyan/20 hover:scale-[1.02] transition-transform"
                    >
                      Use in Chat 💬
                    </button>
                  </div>
                ) : selectedEdge ? (
                  <div className="space-y-4">
                    <span className="text-[10px] font-heading font-bold bg-cyber-magenta/15 border border-cyber-magenta/35 text-cyber-magenta px-2 py-0.5 rounded uppercase">
                      Connection Link properties
                    </span>
                    <div className="flex flex-col gap-2 mt-4">
                      <div>
                        <label className="text-[8px] font-heading font-bold text-cyber-muted uppercase block">Source Entity</label>
                        <span className="text-xs font-semibold text-white">{selectedEdge.fromLabel}</span>
                      </div>
                      <div className="text-cyber-magenta text-xs font-heading font-bold py-1">
                        → {selectedEdge.label || 'RELATED'} →
                      </div>
                      <div>
                        <label className="text-[8px] font-heading font-bold text-cyber-muted uppercase block">Target Entity</label>
                        <span className="text-xs font-semibold text-white">{selectedEdge.toLabel}</span>
                      </div>
                    </div>

                    <div className="bg-zinc-950/60 border border-cyber-border/40 rounded-xl p-4 mt-4">
                      {selectedEdge.properties && Object.keys(selectedEdge.properties).map(key => (
                        <div key={key} className="mb-3">
                          <label className="text-[9px] font-heading font-bold text-cyber-muted uppercase tracking-wider block mb-0.5">{key}</label>
                          <span className="text-xs text-cyber-text block leading-relaxed">{selectedEdge.properties[key]}</span>
                        </div>
                      ))}
                    </div>

                    <button 
                      onClick={() => {
                        const promptText = `Explain the connection: ${selectedEdge.fromLabel} —[${selectedEdge.label || 'RELATED'}]—> ${selectedEdge.toLabel}`
                        handleInjectPrompt(promptText)
                      }}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-magenta text-cyber-bg font-heading font-extrabold text-xs flex items-center justify-center gap-1.5 mt-6 shadow-lg shadow-cyber-cyan/20 hover:scale-[1.02] transition-transform"
                    >
                      Use in Chat 💬
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-80 text-center opacity-60">
                    <HelpCircle className="w-8 h-8 text-cyber-muted mb-2 animate-bounce" />
                    <p className="text-xs text-cyber-muted font-subheading uppercase tracking-widest">
                      Select a node or connection path to probe properties.
                    </p>
                  </div>
                )}
              </div>

              <div className="border-t border-cyber-border/40 pt-4 text-[10px] text-cyber-muted text-center font-subheading">
                Showing live Neo4j AuraDB graph connections
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
