import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { useGenerate } from '../context/GenerateContext'
import ScoreBar from './ScoreBar'

const AGENTS = [
  { key: 'trend_interpreter', name: '趋势解读', icon: '📊' },
  { key: 'strategy_planner', name: '策略规划', icon: '🎯' },
  { key: 'content_writer', name: '内容创作', icon: '✍️' },
  { key: 'quality_reviewer', name: '质量评审', icon: '🔍' },
  { key: 'final_polisher', name: '最终润色', icon: '✨' },
]

const PLATFORM_LABELS = {
  xiaohongshu: '小红书',
  wechat: '微信公众号',
  douyin: '抖音',
}

export default function AgentPanel() {
  const { panelOpen, togglePanel, loading, result, pipelineConfig, setPipelineConfig } = useGenerate()
  const [expandedAgent, setExpandedAgent] = useState(null)
  const [activeTab, setActiveTab] = useState('output')
  const [prompts, setPrompts] = useState({})
  const [editingPrompt, setEditingPrompt] = useState({})
  const [saveStatus, setSaveStatus] = useState({})
  const [configOpen, setConfigOpen] = useState(false)
  const [simulatedStep, setSimulatedStep] = useState(-1)
  const timerRef = useRef(null)

  // Load prompts on mount
  useEffect(() => {
    api.getPrompts().then((data) => {
      const map = {}
      data.forEach((p) => { map[p.name] = p.content })
      setPrompts(map)
    }).catch(() => {})
  }, [])

  // Simulate agent progression during loading
  useEffect(() => {
    if (loading) {
      setSimulatedStep(0)
      let step = 0
      timerRef.current = setInterval(() => {
        step++
        if (step < AGENTS.length) {
          setSimulatedStep(step)
        } else {
          clearInterval(timerRef.current)
        }
      }, 3000)
    } else {
      clearInterval(timerRef.current)
      setSimulatedStep(-1)
    }
    return () => clearInterval(timerRef.current)
  }, [loading])

  const getAgentStatus = (idx) => {
    if (loading) {
      if (idx < simulatedStep) return 'complete'
      if (idx === simulatedStep) return 'running'
      return 'idle'
    }
    if (result?.metrics?.agents?.length > 0) {
      const hasMetric = result.metrics.agents.some((m) => m.agent_name === AGENTS[idx].key && m.duration_seconds > 0)
      return hasMetric ? 'complete' : 'idle'
    }
    return 'idle'
  }

  const getAgentMetric = (agentKey) => {
    return result?.metrics?.agents?.find((m) => m.agent_name === agentKey) || null
  }

  const handleToggleAgent = (key) => {
    setExpandedAgent((prev) => (prev === key ? null : key))
    setActiveTab('output')
    setSaveStatus({})
  }

  const handleSavePrompt = async (name) => {
    const content = editingPrompt[name]
    if (content === undefined) return
    setSaveStatus((s) => ({ ...s, [name]: 'saving' }))
    try {
      await api.updatePrompt(name, content)
      setPrompts((p) => ({ ...p, [name]: content }))
      setEditingPrompt((e) => { const n = { ...e }; delete n[name]; return n })
      setSaveStatus((s) => ({ ...s, [name]: 'saved' }))
      setTimeout(() => setSaveStatus((s) => { const n = { ...s }; delete n[name]; return n }), 2000)
    } catch {
      setSaveStatus((s) => ({ ...s, [name]: 'error' }))
    }
  }

  const handleResetPrompt = (name) => {
    setEditingPrompt((e) => { const n = { ...e }; delete n[name]; return n })
    setSaveStatus((s) => { const n = { ...s }; delete n[name]; return n })
  }

  const getEditedContent = (name) => {
    return editingPrompt[name] !== undefined ? editingPrompt[name] : (prompts[name] || '')
  }

  if (!panelOpen) return null

  return (
    <div className="agent-panel">
      <div className="agent-panel__header">
        <h3 className="agent-panel__title">智能体管线</h3>
        <button className="modal__close" onClick={togglePanel}>&times;</button>
      </div>

      <div className="agent-panel__body">
        {/* Pipeline Timeline */}
        <div className="pipeline-timeline">
          {AGENTS.map((agent, idx) => {
            const status = getAgentStatus(idx)
            const metric = getAgentMetric(agent.key)
            const isExpanded = expandedAgent === agent.key
            return (
              <div key={agent.key} className="pipeline-timeline__item">
                {idx < AGENTS.length - 1 && (
                  <div className={`pipeline-timeline__line ${status === 'complete' ? 'pipeline-timeline__line--done' : ''}`} />
                )}
                <div
                  className={`pipeline-timeline__node pipeline-timeline__node--${status} ${isExpanded ? 'pipeline-timeline__node--selected' : ''}`}
                  onClick={() => handleToggleAgent(agent.key)}
                >
                  <div className="pipeline-timeline__circle">
                    <span className="pipeline-timeline__icon">{agent.icon}</span>
                  </div>
                  <div className="pipeline-timeline__info">
                    <span className="pipeline-timeline__name">{agent.name}</span>
                    <span className="pipeline-timeline__status">
                      {status === 'running' && <span className="pipeline-timeline__pulse" />}
                      {status === 'complete' && metric && (
                        <span className="pipeline-timeline__metric">{metric.duration_seconds.toFixed(2)}s</span>
                      )}
                      {status === 'idle' && <span className="pipeline-timeline__idle-text">等待中</span>}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Expanded Agent Detail */}
        {expandedAgent && (
          <AgentDetail
            agentKey={expandedAgent}
            agent={AGENTS.find((a) => a.key === expandedAgent)}
            result={result}
            metric={getAgentMetric(expandedAgent)}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            promptContent={getEditedContent(expandedAgent)}
            editingPrompt={editingPrompt}
            setEditingPrompt={setEditingPrompt}
            saveStatus={saveStatus[expandedAgent]}
            onSave={() => handleSavePrompt(expandedAgent)}
            onReset={() => handleResetPrompt(expandedAgent)}
          />
        )}

        {/* Pipeline Config */}
        <div className="pipeline-config">
          <button
            className="pipeline-config__toggle"
            onClick={() => setConfigOpen((o) => !o)}
          >
            <span>管线配置</span>
            <span className={`pipeline-config__arrow ${configOpen ? 'pipeline-config__arrow--open' : ''}`}>&#9660;</span>
          </button>
          {configOpen && (
            <div className="pipeline-config__body">
              <div className="pipeline-config__field">
                <label className="pipeline-config__label">
                  评审阈值
                  <span className="pipeline-config__value">{pipelineConfig.scoreThreshold}</span>
                </label>
                <input
                  type="range"
                  min="60"
                  max="100"
                  step="5"
                  value={pipelineConfig.scoreThreshold}
                  onChange={(e) => setPipelineConfig((c) => ({ ...c, scoreThreshold: Number(e.target.value) }))}
                  className="pipeline-config__slider"
                />
                <div className="pipeline-config__range">
                  <span>60</span><span>100</span>
                </div>
              </div>
              <div className="pipeline-config__field">
                <label className="pipeline-config__label">
                  最大改写轮次
                  <span className="pipeline-config__value">{pipelineConfig.maxCycles}</span>
                </label>
                <div className="pipeline-config__cycles">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      className={`pipeline-config__cycle-btn ${pipelineConfig.maxCycles === n ? 'pipeline-config__cycle-btn--active' : ''}`}
                      onClick={() => setPipelineConfig((c) => ({ ...c, maxCycles: n }))}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
              <p className="pipeline-config__hint">
                低于阈值的文案将自动改写，最多循环指定轮次
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AgentDetail({
  agentKey, agent, result, metric, activeTab, setActiveTab,
  promptContent, editingPrompt, setEditingPrompt, saveStatus, onSave, onReset,
}) {
  const isEditing = editingPrompt[agentKey] !== undefined

  return (
    <div className="agent-detail">
      <div className="agent-detail__header">
        <span className="agent-detail__icon">{agent.icon}</span>
        <span className="agent-detail__name">{agent.name}</span>
        {metric && (
          <div className="agent-detail__metrics">
            {metric.total_tokens > 0 && (
              <span className="agent-detail__token-badge">{metric.total_tokens.toLocaleString()} tk</span>
            )}
          </div>
        )}
      </div>

      <div className="agent-detail__tabs">
        <button
          className={`agent-detail__tab ${activeTab === 'output' ? 'agent-detail__tab--active' : ''}`}
          onClick={() => setActiveTab('output')}
        >
          输出
        </button>
        <button
          className={`agent-detail__tab ${activeTab === 'prompt' ? 'agent-detail__tab--active' : ''}`}
          onClick={() => setActiveTab('prompt')}
        >
          提示词
        </button>
      </div>

      <div className="agent-detail__content">
        {activeTab === 'output' ? (
          <AgentOutput agentKey={agentKey} result={result} />
        ) : (
          <div className="prompt-editor">
            <textarea
              className="prompt-editor__textarea"
              value={isEditing ? editingPrompt[agentKey] : promptContent}
              onChange={(e) => setEditingPrompt((prev) => ({ ...prev, [agentKey]: e.target.value }))}
              spellCheck={false}
            />
            <div className="prompt-editor__actions">
              {isEditing ? (
                <>
                  <button className="btn btn-primary btn-sm" onClick={onSave} disabled={saveStatus === 'saving'}>
                    {saveStatus === 'saving' ? '保存中...' : saveStatus === 'saved' ? '已保存' : '保存'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={onReset}>重置</button>
                </>
              ) : (
                <span className="prompt-editor__status">点击文本区域开始编辑</span>
              )}
              {saveStatus === 'error' && <span className="prompt-editor__error">保存失败</span>}
            </div>
            <div className="prompt-editor__placeholders">
              <span className="prompt-editor__ph-label">占位变量:</span>
              {extractPlaceholders(promptContent).map((ph) => (
                <code key={ph} className="prompt-editor__ph">{`{${ph}}`}</code>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function AgentOutput({ agentKey, result }) {
  if (!result) {
    return <div className="agent-detail__empty">生成后可查看输出</div>
  }

  switch (agentKey) {
    case 'trend_interpreter':
      return <TrendProfileOutput profile={result.trend_profile} />
    case 'strategy_planner':
      return <StrategiesOutput strategies={result.strategies} />
    case 'content_writer':
      return <DraftsOutput drafts={result.drafts} />
    case 'quality_reviewer':
      return <ReviewOutput scores={result.review_scores} feedback={result.review_feedback} />
    case 'final_polisher':
      return <FinalOutput content={result.final_content} titles={result.title_options} />
    default:
      return <div className="agent-detail__empty">暂无数据</div>
  }
}

function TrendProfileOutput({ profile }) {
  if (!profile) return <div className="agent-detail__empty">未执行</div>
  const items = [
    { label: '核心事件', value: profile.core_event },
    { label: '情感倾向', value: profile.sentiment },
    { label: '关键数据', value: Array.isArray(profile.key_data) ? profile.key_data.join('、') : profile.key_data },
    { label: '内容角度', value: Array.isArray(profile.angles) ? profile.angles.join('、') : profile.angles },
  ]
  return (
    <div className="agent-output__kv-list">
      {items.map((item) => (
        <div key={item.label} className="agent-output__kv">
          <span className="agent-output__label">{item.label}</span>
          <span className="agent-output__value">{item.value || '-'}</span>
        </div>
      ))}
    </div>
  )
}

function StrategiesOutput({ strategies }) {
  if (!strategies || !Object.keys(strategies).length) return <div className="agent-detail__empty">未执行</div>
  return (
    <div className="agent-output__platform-list">
      {Object.entries(strategies).map(([platform, s]) => (
        <div key={platform} className="agent-output__platform-card">
          <div className="agent-output__platform-header">
            <span className="badge badge-gold">{PLATFORM_LABELS[platform] || platform}</span>
          </div>
          <div className="agent-output__kv">
            <span className="agent-output__label">切入角度</span>
            <span className="agent-output__value">{s.angle}</span>
          </div>
          <div className="agent-output__kv">
            <span className="agent-output__label">目标受众</span>
            <span className="agent-output__value">{s.audience}</span>
          </div>
          {s.structure && (
            <div className="agent-output__kv">
              <span className="agent-output__label">结构</span>
              <span className="agent-output__value">
                {typeof s.structure === 'string' ? s.structure : `Hook: ${s.structure.hook} / Body: ${s.structure.body} / CTA: ${s.structure.cta}`}
              </span>
            </div>
          )}
          <div className="agent-output__kv">
            <span className="agent-output__label">情感钩子</span>
            <span className="agent-output__value">{s.emotion_hook}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function DraftsOutput({ drafts }) {
  if (!drafts || !Object.keys(drafts).length) return <div className="agent-detail__empty">未执行</div>
  return (
    <div className="agent-output__draft-list">
      {Object.entries(drafts).map(([platform, text]) => (
        <div key={platform} className="agent-output__draft">
          <span className="badge badge-gold" style={{ marginBottom: 8 }}>{PLATFORM_LABELS[platform] || platform}</span>
          <div className="agent-output__draft-text">{text}</div>
        </div>
      ))}
    </div>
  )
}

function ReviewOutput({ scores, feedback }) {
  if (!scores || !Object.keys(scores).length) return <div className="agent-detail__empty">未执行</div>
  return (
    <div className="agent-output__review-list">
      {Object.entries(scores).map(([platform, score]) => (
        <div key={platform} className="agent-output__review-item">
          <div className="agent-output__review-header">
            <span className="badge badge-gold">{PLATFORM_LABELS[platform] || platform}</span>
          </div>
          <ScoreBar score={score} />
          {feedback?.[platform] && (
            <div className="agent-output__feedback">{feedback[platform]}</div>
          )}
        </div>
      ))}
    </div>
  )
}

function FinalOutput({ content, titles }) {
  if (!content || !Object.keys(content).length) return <div className="agent-detail__empty">未执行</div>
  return (
    <div className="agent-output__final-list">
      {Object.entries(content).map(([platform, text]) => (
        <div key={platform} className="agent-output__final-item">
          <span className="badge badge-gold" style={{ marginBottom: 8 }}>{PLATFORM_LABELS[platform] || platform}</span>
          <div className="agent-output__draft-text">{text}</div>
          {titles?.[platform]?.length > 0 && (
            <div className="agent-output__titles">
              <span className="agent-output__label" style={{ marginBottom: 4 }}>标题方案</span>
              {titles[platform].map((t, i) => (
                <div key={i} className="agent-output__title-item">{typeof t === 'string' ? t : t.title || t.text}</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function extractPlaceholders(content) {
  if (!content) return []
  const matches = content.match(/\{(\w+)\}/g)
  if (!matches) return []
  return [...new Set(matches.map((m) => m.slice(1, -1)))]
}
