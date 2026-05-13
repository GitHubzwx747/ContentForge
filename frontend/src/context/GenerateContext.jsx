import { createContext, useContext, useState, useCallback } from 'react'

const GenerateContext = createContext(null)

export function GenerateProvider({ children }) {
  const [text, setText] = useState('')
  const [selected, setSelected] = useState(['xiaohongshu'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const [pipelineConfig, setPipelineConfig] = useState({
    scoreThreshold: 85,
    maxCycles: 2,
  })

  const togglePlatform = useCallback((key) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  }, [])

  const togglePanel = useCallback(() => {
    setPanelOpen((prev) => !prev)
  }, [])

  const resetGeneration = useCallback(() => {
    setText('')
    setSelected(['xiaohongshu'])
    setLoading(false)
    setResult(null)
    setError(null)
  }, [])

  return (
    <GenerateContext.Provider
      value={{
        text, setText,
        selected, togglePlatform,
        loading, setLoading,
        result, setResult,
        error, setError,
        resetGeneration,
        panelOpen, togglePanel,
        pipelineConfig, setPipelineConfig,
      }}
    >
      {children}
    </GenerateContext.Provider>
  )
}

export function useGenerate() {
  const ctx = useContext(GenerateContext)
  if (!ctx) throw new Error('useGenerate must be inside GenerateProvider')
  return ctx
}
