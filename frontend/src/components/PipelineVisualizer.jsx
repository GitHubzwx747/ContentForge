const AGENTS = [
  { key: 'analyst',    label: '热点解读', icon: '🔍' },
  { key: 'strategist', label: '策略规划', icon: '🎯' },
  { key: 'writer',     label: '文案创作', icon: '✍️' },
  { key: 'reviewer',   label: '质量评审', icon: '📋' },
  { key: 'polisher',   label: '终稿打磨', icon: '✨' },
]

export default function PipelineVisualizer({ agents, isRunning, isComplete }) {
  // Determine which agents are done / active from the agents array (if provided)
  // Each agent in the array may have { name, duration, status, ... }
  const completedNames = new Set()
  let activeName = null

  if (isComplete && agents?.length) {
    // All done
    agents.forEach((a) => completedNames.add(a.name || a.agent || a.key))
  } else if (isRunning) {
    // Simulate: if no per-agent data, just light up sequentially based on time
    // We'll mark agents as active/completed based on whether they appear in the array
    if (agents?.length) {
      agents.forEach((a, i) => {
        const name = a.name || a.agent || a.key
        if (i < agents.length - 1) {
          completedNames.add(name)
        } else {
          activeName = name
        }
      })
    } else {
      // No per-agent info — just show the pipeline in "running" state
      // Cycle through agents based on elapsed time (cosmetic only)
      activeName = '__first__'
    }
  }

  function getState(agentKey, agentLabel) {
    if (isComplete) return 'complete'
    if (!isRunning) return 'idle'

    // If we have explicit agent data
    if (agents?.length) {
      if (completedNames.has(agentKey) || completedNames.has(agentLabel)) return 'complete'
      if (activeName === agentKey || activeName === agentLabel) return 'active'
      return 'idle'
    }

    // No per-agent data — show first as active when running
    if (activeName === '__first__' && agentKey === AGENTS[0].key) return 'active'
    return 'idle'
  }

  function getLineState(idx) {
    if (isComplete) return 'complete'
    if (!isRunning) return 'idle'

    if (agents?.length) {
      // Line after index idx connects AGENTS[idx] → AGENTS[idx+1]
      // If AGENTS[idx] is complete, the line is active
      const src = AGENTS[idx]
      if (completedNames.has(src.key) || completedNames.has(src.label)) return 'complete'
      // If source is active, line is animating
      const srcState = getState(src.key, src.label)
      if (srcState === 'active') return 'active'
    } else if (activeName === '__first__' && idx === 0) {
      return 'active'
    }

    return 'idle'
  }

  // Detect if quality review triggered rewrite (look for rewrite/loop indicators)
  const hasRewrite = agents?.some(
    (a) => a.rewrite || a.loops > 1 || a.iterations > 1
  )

  return (
    <div className="pipeline">
      {AGENTS.map((agent, idx) => {
        const state = getState(agent.key, agent.label)
        const isRewriteNode = hasRewrite && agent.key === 'reviewer'

        return (
          <div key={agent.key} style={{ display: 'contents' }}>
            <div className={`pipeline__node pipeline__node--${state}`}>
              <div className="pipeline__node-circle">
                {state === 'complete' ? (
                  <span style={{ color: 'var(--success)', fontSize: '1.4rem' }}>&#10003;</span>
                ) : state === 'active' ? (
                  <div className="spinner" />
                ) : (
                  <span className="pipeline__node-icon">{agent.icon}</span>
                )}
              </div>
              <span className="pipeline__node-label">{agent.label}</span>
              {isRewriteNode && state !== 'idle' && (
                <span className="pipeline__rewrite-indicator">&#8635; 重写中</span>
              )}
            </div>
            {idx < AGENTS.length - 1 && (
              <div className={`pipeline__line pipeline__line--${getLineState(idx)}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
