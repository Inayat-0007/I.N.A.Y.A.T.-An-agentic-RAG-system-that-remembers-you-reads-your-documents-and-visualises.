import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Sparkles, Database, ShieldAlert, Layers } from 'lucide-react'
import { motion } from 'framer-motion'

export default function LandingPage({ onEnterWorkspace }) {
  const canvasRef = useRef(null)
  const [nameInput, setNameInput] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  // Animated particle background
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animationFrameId

    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const particles = []
    const particleCount = 75
    const connectionDistance = 120

    class Particle {
      constructor() {
        this.x = Math.random() * width
        this.y = Math.random() * height
        this.vx = (Math.random() - 0.5) * 0.7
        this.vy = (Math.random() - 0.5) * 0.7
        this.radius = Math.random() * 2 + 1.5
        this.color = Math.random() > 0.5 ? '#00F0FF' : '#FF00E5'
      }

      update() {
        this.x += this.vx
        this.y += this.vy

        if (this.x < 0 || this.x > width) this.vx = -this.vx
        if (this.y < 0 || this.y > height) this.vy = -this.vy
      }

      draw() {
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
        ctx.fillStyle = this.color
        ctx.shadowBlur = 8
        ctx.shadowColor = this.color
        ctx.fill()
        ctx.shadowBlur = 0 // reset
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle())
    }

    const drawConnections = () => {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < connectionDistance) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            const alpha = (1 - dist / connectionDistance) * 0.25
            ctx.strokeStyle = `rgba(167, 139, 250, ${alpha})`
            ctx.lineWidth = 1
            ctx.stroke()
          }
        }
      }
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height)
      
      // Draw a radial gradient background overlay
      const grad = ctx.createRadialGradient(width/2, height/2, 10, width/2, height/2, width*0.7)
      grad.addColorStop(0, '#0c0b1c')
      grad.addColorStop(1, '#040408')
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, width, height)

      particles.forEach(p => {
        p.update()
        p.draw()
      })
      drawConnections()

      animationFrameId = requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (nameInput.trim()) {
      onEnterWorkspace(nameInput.trim())
    } else {
      setErrorMsg("Please provide a name to access the agent workspace.")
    }
  }

  return (
    <div className="relative min-h-[90vh] flex flex-col items-center justify-center py-12 px-6">
      {/* Background canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full object-cover z-0 pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 max-w-4xl w-full text-center flex flex-col items-center mt-8">
        
        {/* Typewriter Neon Title */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-2"
        >
          <span className="px-3 py-1 text-xs font-heading font-semibold tracking-wider text-cyber-cyan border border-cyber-cyan/30 bg-cyber-cyan/10 rounded-full uppercase">
            Cognitive Retrieval Augmented Generation
          </span>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-6xl md:text-8xl font-heading font-black tracking-tighter mb-4 text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan via-purple-400 to-cyber-magenta filter drop-shadow-[0_4px_20px_rgba(0,240,255,0.25)]"
        >
          I.N.A.Y.A.T.
        </motion.h1>

        {/* Dynamic Typewriter text block */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-base md:text-lg font-subheading text-cyber-muted max-w-xl mb-10 leading-relaxed font-light"
        >
          An agentic RAG system that <span className="text-white font-medium border-b border-cyber-cyan/40">remembers you</span>, reads your <span className="text-white font-medium border-b border-cyber-cyan/40 font-heading">documents</span>, and visualises its <span className="text-white font-medium border-b border-cyber-magenta/40">knowledge graph</span> in real time.
        </motion.p>

        {/* Glassmorphism Credentials Selector */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="w-full max-w-md p-8 rounded-2xl glass-glow-cyan mb-12 shadow-2xl relative"
        >
          <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 px-3 py-0.5 rounded bg-cyber-cyan text-cyber-bg font-heading text-[10px] font-bold uppercase tracking-wider">
            Workspace Gateway
          </div>
          
          <h3 className="text-sm font-subheading font-bold text-cyber-text mb-4 uppercase tracking-widest text-center flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-cyber-cyan" /> Initialize Demo Workspace
          </h3>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              id="landing-user-input"
              type="text"
              placeholder="Enter active profile name (e.g. Moham)"
              value={nameInput}
              onChange={(e) => {
                setNameInput(e.target.value)
                setErrorMsg('')
              }}
              className="w-full px-4 py-3 rounded-xl bg-cyber-bg/70 border border-cyber-border text-white placeholder-cyber-muted text-sm font-subheading text-center focus:outline-none focus:border-cyber-cyan focus:shadow-[0_0_15px_rgba(0,240,255,0.25)] transition-all duration-300"
            />
            {errorMsg && (
              <p className="text-xs text-cyber-magenta font-semibold mt-1">⚠️ {errorMsg}</p>
            )}
            
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-heading font-black text-sm text-cyber-bg bg-gradient-to-r from-cyber-cyan to-cyber-magenta hover:from-cyber-magenta hover:to-cyber-cyan hover:scale-[1.02] shadow-lg hover:shadow-cyber-cyan/35 transition-all duration-300 group"
            >
              Access Agentic Workspace <ArrowRight className="w-4 h-4 text-cyber-bg transition-transform duration-200 group-hover:translate-x-1" />
            </button>
          </form>
        </motion.div>

        {/* 2026 Core Pillars Stats Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl w-full border-t border-cyber-border/40 pt-8"
        >
          <div className="flex flex-col items-center p-3 rounded-xl bg-white/[0.02] border border-cyber-border/20">
            <span className="font-heading font-extrabold text-2xl text-cyber-cyan text-glow-cyan">19/19</span>
            <span className="text-xs text-cyber-muted font-subheading mt-1">Smoke Tests OK</span>
          </div>
          <div className="flex flex-col items-center p-3 rounded-xl bg-white/[0.02] border border-cyber-border/20">
            <div className="flex items-center gap-1">
              <Database className="w-4 h-4 text-purple-400" />
              <span className="font-heading font-extrabold text-2xl text-purple-400">3 Cloud</span>
            </div>
            <span className="text-xs text-cyber-muted font-subheading mt-1">Integrations</span>
          </div>
          <div className="flex flex-col items-center p-3 rounded-xl bg-white/[0.02] border border-cyber-border/20">
            <div className="flex items-center gap-1">
              <ShieldAlert className="w-4 h-4 text-cyber-magenta animate-pulse" />
              <span className="font-heading font-extrabold text-2xl text-cyber-magenta text-glow-magenta">Active</span>
            </div>
            <span className="text-xs text-cyber-muted font-subheading mt-1">Self-Healing CB</span>
          </div>
          <div className="flex flex-col items-center p-3 rounded-xl bg-white/[0.02] border border-cyber-border/20">
            <div className="flex items-center gap-1">
              <Layers className="w-4 h-4 text-cyber-gold" />
              <span className="font-heading font-extrabold text-2xl text-cyber-gold">Isolated</span>
            </div>
            <span className="text-xs text-cyber-muted font-subheading mt-1">User Workspace</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
