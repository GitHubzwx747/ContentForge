import { useState, useCallback } from 'react'
import { api } from '../api/client'
import PipelineVisualizer from '../components/PipelineVisualizer'
import PlatformTabs from '../components/PlatformTabs'
import ScoreBar from '../components/ScoreBar'

const PLATFORMS = [
  { key: 'xiaohongshu', label: '小红书' },
  { key: 'wechat',      label: '微信公众号' },
  { key: 'douyin',      label: '抖音' },
]

export default function Generate() {
  const [text, setText] = useState('')
  const [selected, setSelected] = useState(['xiaohongshu'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const togglePlatform = useCallback((key) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  }, [])

  const handleGenerate = async () => {
    if (!text.trim() || !selected.length || loading) return
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const res = await api.generate(text.trim(), selected)
      setResult(res)
    } catch (err) {
      setError(err.message || '生成失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async (txt, id) => {
    try {
      await navigator.clipboard.writeText(txt)
      return true
    } catch {
      return false
    }
  }

  const platformKeys = result?.platforms || []
  const agents = result?.metrics?.agents

  return (
    <div>
      <div className="page-header animate-in">
        <h1>生成文案</h1>
        <p>输入热点内容，AI 多智能体协作为你创作平台专属文案</p>
      </div>

      {error && (
        <div className="error-banner animate-in">
          <span>&#9888;</span> {error}
        </div>
      )}

      <div className="generate-input animate-in-delay-1">
        <textarea
          className="textarea"
          placeholder="粘贴热点内容，或输入话题..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
        />
        <div className="generate-controls">
          <div className="platform-toggles">
            {PLATFORMS.map((p) => (
              <button
                key={p.key}
                className={`platform-chip ${selected.includes(p.key) ? 'active' : ''}`}
                onClick={() => togglePlatform(p.key)}
                disabled={loading}
              >
                {p.label}
              </button>
            ))}
          </div>
          <button
            className="btn btn-primary generate-btn"
            onClick={handleGenerate}
            disabled={loading || !text.trim() || !selected.length}
          >
            {loading ? '生成中...' : '生成文案'}
          </button>
        </div>
      </div>

      <PipelineVisualizer
        agents={agents}
        isRunning={loading}
        isComplete={!!result && !loading}
      />

      {result && !loading && platformKeys.length > 0 && (
        <div className="results-section animate-in">
          <PlatformTabs platforms={platformKeys}>
            {(activePlatform) => {
              const content = result?.final_content?.[activePlatform] || ''
              const titles = result?.title_options?.[activePlatform] || []
              const score = result?.review_scores?.[activePlatform] || 0
              const metrics = result?.metrics || {}

              return (
                <>
                  <div className="result-block">
                    <div className="result-block__label">生成内容</div>
                    <div className="result-block__text">{content}</div>
                  </div>

                  {titles.length > 0 && (
                    <div className="result-block">
                      <div className="result-block__label">标题方案</div>
                      <div className="result-block__titles">
                        {titles.map((t, i) => (
                          <CopyableTitle
                            key={i}
                            text={typeof t === 'string' ? t : t.title || t.text}
                            onCopy={handleCopy}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {score > 0 && (
                    <div className="result-block">
                      <div className="result-block__label">评审评分</div>
                      <ScoreBar score={score} />
                    </div>
                  )}

                  {(metrics.total_tokens || metrics.total_duration) && (
                    <div className="metrics-row">
                      {metrics.total_tokens > 0 && (
                        <div className="metric-item">
                          <span className="metric-item__label">Token</span>
                          <span className="metric-item__value">{metrics.total_tokens.toLocaleString()}</span>
                        </div>
                      )}
                      {metrics.total_duration > 0 && (
                        <div className="metric-item">
                          <span className="metric-item__label">耗时</span>
                          <span className="metric-item__value">
                            {metrics.total_duration.toFixed(1)}s
                          </span>
                        </div>
                      )}
                      {metrics.average_score > 0 && (
                        <div className="metric-item">
                          <span className="metric-item__label">平均评分</span>
                          <span className="metric-item__value">{metrics.average_score}</span>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )
            }}
          </PlatformTabs>
        </div>
      )}
    </div>
  )
}

function CopyableTitle({ text, onCopy }) {
  const [copied, setCopied] = useState(false)

  const handleClick = async () => {
    const ok = await onCopy(text)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="result-title-row">
      <span className="result-title-text">{text}</span>
      <button
        className={`btn-copy ${copied ? 'btn-copy--copied' : ''}`}
        onClick={handleClick}
      >
        {copied ? '已复制' : '复制'}
      </button>
    </div>
  )
}
