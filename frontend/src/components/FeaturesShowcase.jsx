import React from 'react'
import { Brain, Network, ShieldCheck, Share2, ToggleLeft, UserCheck, Terminal, Award } from 'lucide-react'
import { motion } from 'framer-motion'

export default function FeaturesShowcase() {
  const features = [
    {
      icon: <Brain className="w-6 h-6 text-cyber-cyan" />,
      title: "Persistent Memory",
      desc: "Integrates Mem0 API to remember user facts and preference context across browser refreshes and restart instances."
    },
    {
      icon: <Network className="w-6 h-6 text-purple-400" />,
      title: "Neo4j Graph RAG",
      desc: "Harnesses LlamaIndex PropertyGraphIndex on Neo4j AuraDB to link document chunks to specific entity nodes."
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-green-400" />,
      title: "Self-Healing Architecture",
      desc: "Uses custom active circuit breakers to gracefully route queries, bypassing failed databases dynamically."
    },
    {
      icon: <Share2 className="w-6 h-6 text-cyber-magenta" />,
      title: "Interactive Graph Drawer",
      desc: "Visualizes live database relationship charts with Vis.js networks. Inject prompts from nodes directly into chat."
    },
    {
      icon: <ToggleLeft className="w-6 h-6 text-cyber-gold" />,
      title: "Resilience Testing Panel",
      desc: "Enables manual force-fail toggle triggers in the sidebar UI, offering visible verification of circuit isolation loops."
    },
    {
      icon: <UserCheck className="w-6 h-6 text-blue-400" />,
      title: "Dynamic Profile Isolation",
      desc: "Stores separate user data directories and chat histories, linked using browser session query strings."
    },
    {
      icon: <Terminal className="w-6 h-6 text-zinc-400" />,
      title: "One-Click Execution",
      desc: "Bundles direct runtime launchers alongside multi-stage Docker configurations for instant container deployments."
    },
    {
      icon: <Award className="w-6 h-6 text-amber-500" />,
      title: "Industrial Code Quality",
      desc: "Backed by 19/19 passing test suites (smoke checks, imports validation, and mocks verification) in CI pipelines."
    }
  ]

  return (
    <section className="py-20 px-6 max-w-6xl mx-auto border-t border-cyber-border/40 relative">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-5xl font-heading font-black mb-4 tracking-wider uppercase text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan to-cyber-magenta">
          Engine Capabilities
        </h2>
        <p className="text-sm font-subheading text-cyber-muted max-w-xl mx-auto font-light">
          A high-performance feature set designed to deliver robust, uninterrupted RAG execution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((f, idx) => (
          <motion.div
            key={idx}
            whileHover={{ y: -6, scale: 1.01 }}
            transition={{ type: 'spring', stiffness: 300 }}
            className="p-6 rounded-2xl glass border border-cyber-border hover:border-cyber-cyan/50 hover:shadow-[0_8px_30px_rgba(0,240,255,0.08)] transition-all duration-300 relative group"
          >
            {/* Hover Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-cyber-cyan/0 to-cyber-cyan/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
            
            <div className="w-12 h-12 rounded-xl bg-white/[0.04] border border-cyber-border/40 flex items-center justify-center mb-5 group-hover:scale-110 group-hover:border-cyber-cyan/60 transition-all duration-300">
              {f.icon}
            </div>
            
            <h3 className="text-base font-heading font-bold mb-2 text-white group-hover:text-cyber-cyan transition-colors">
              {f.title}
            </h3>
            
            <p className="text-xs text-cyber-muted leading-relaxed font-light font-body">
              {f.desc}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
