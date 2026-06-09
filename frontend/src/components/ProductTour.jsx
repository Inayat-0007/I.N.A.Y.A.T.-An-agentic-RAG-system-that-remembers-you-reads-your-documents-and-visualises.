import React, { useState } from 'react'
import { Sparkles, ArrowRight, X, Cpu, ShieldAlert, Database, Share2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ProductTour({ onClose }) {
  const [stepIdx, setStepIdx] = useState(0)

  const tourSteps = [
    {
      icon: <Cpu className="w-8 h-8 text-cyber-cyan animate-pulse" />,
      title: "Isolated Workspaces",
      desc: "Enter your name (e.g. Rahul) in the user switcher. This creates an isolated folder path and updates your browser URL parameter so that your chats, files, and database indexes are completely isolated."
    },
    {
      icon: <Database className="w-8 h-8 text-purple-400" />,
      title: "Unified RAG Ingestion",
      desc: "Drop PDF or TXT files directly into the upload slot. The system automatically loads documents, chunks them, attaches your user metadata, and updates your Neo4j property graph index."
    },
    {
      icon: <ShieldAlert className="w-8 h-8 text-cyber-magenta animate-bounce" />,
      title: "Fault Tolerance Testing",
      desc: "Blow the active circuit breakers in the sidebar. This simulates Neo4j AuraDB or Mem0 Cloud outages, letting you verify that the pipeline falls back gracefully to direct LLM execution without throwing exceptions."
    },
    {
      icon: <Share2 className="w-8 h-8 text-cyber-gold animate-spin-slow" />,
      title: "Interactive Neural Graph",
      desc: "Open the visualization canvas to inspect database relationships. Click nodes or links to review metadata attributes, and click 'Use in Chat' to instantly prompt the agent with the selected entity relationship!"
    }
  ]

  const current = tourSteps[stepIdx]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-filter backdrop-blur-sm select-text">
      <AnimatePresence mode="wait">
        <motion.div
          key={stepIdx}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="max-w-md w-full p-8 rounded-2xl glass-glow-cyan shadow-2xl relative border border-cyber-cyan/35"
        >
          {/* Close button */}
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-cyber-muted hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex flex-col items-center text-center">
            
            {/* Step icon */}
            <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-cyber-border flex items-center justify-center mb-6">
              {current.icon}
            </div>

            <span className="text-[10px] font-heading font-extrabold text-cyber-cyan tracking-widest uppercase mb-1">
              Step {stepIdx + 1} of {tourSteps.length}
            </span>

            <h3 className="text-xl font-heading font-black text-white mb-3 tracking-wide">
              {current.title}
            </h3>

            <p className="text-xs text-cyber-muted leading-relaxed font-light font-body mb-8">
              {current.desc}
            </p>

            {/* Navigation options */}
            <div className="flex justify-between items-center w-full border-t border-cyber-border/40 pt-4">
              <button 
                onClick={onClose}
                className="text-xs font-heading font-bold text-cyber-muted hover:text-white transition-colors"
              >
                Skip Tour
              </button>

              <div className="flex gap-1">
                {tourSteps.map((_, idx) => (
                  <div 
                    key={idx} 
                    className={`w-1.5 h-1.5 rounded-full transition-all duration-200 ${idx === stepIdx ? 'bg-cyber-cyan w-3' : 'bg-zinc-700'}`} 
                  />
                ))}
              </div>

              {stepIdx < tourSteps.length - 1 ? (
                <button
                  onClick={() => setStepIdx(stepIdx + 1)}
                  className="flex items-center gap-1 text-xs font-heading font-bold text-cyber-cyan hover:text-white transition-colors"
                >
                  Next <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button
                  onClick={onClose}
                  className="px-4 py-1.5 bg-cyber-cyan text-cyber-bg text-xs font-heading font-black rounded-lg shadow-md hover:scale-102 transition-transform"
                >
                  Get Started!
                </button>
              )}
            </div>

          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
