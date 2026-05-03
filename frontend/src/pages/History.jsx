import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PlatformTabs from '../components/PlatformTabs'
import ScoreBar from '../components/ScoreBar'

const PLATFORM_LABELS = {
  xiaohongshu: '小红书',
  wechat: '微信公众号',
  douyin: '抖音',
}

export default function History() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.getHistory(50)
      .then((data) => {
        if (!cancelled) setItems(Array.isArray(data) ? data : data.items || [])
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const handleSelect = async (item) => {
    if (item.results || item.platforms) {
      setSelected(item)
      return
    }
    try {
      const detail = await api.getGeneration(item.id)
      setSelected(detail)
    } catch {
      setSelected(item)
    }
  }

  const formatDate = (d) => {
    if (!d) return ''
    const date = new Date(d)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const parseJson = (val) => {
    if (typeof val === 'string') { try { return JSON.parse(val) } catch { return val } }
    return val
  }

  const getPlatforms = (item) => {
    const p = parseJson(item.platforms)
    return Array.isArray(p) ? p : []
  }

  const getPreview = (item) => {
    return item.trend_markdown || ''
  }

  const getAvgScore = (item) => {
    const scores = parseJson(item.review_scores)
    if (!scores || typeof scores !== 'object') return 0
    const vals = Object.values(scores).filter(Boolean)
    if (!vals.length) return 0
    return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1>历史记录</h1>
          <p>查看过往生成的文案内容</p>
        </div>
        <div className="empty-state">
          <div className="spinner" />
          <span>加载中...</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header animate-in">
        <h1>历史记录</h1>
        <p>查看过往生成的文案内容</p>
      </div>

      {error && <div className="error-banner animate-in">{error}</div>}

      {items.length === 0 ? (
        <div className="empty-state animate-in-delay-1">
          <span style={{ fontSize: '2rem' }}>&#128221;</span>
          <span>暂无历史记录，去生成第一篇文案吧</span>
        </div>
      ) : (
        <div className="history-grid">
          {items.map((item, idx) => (
            <div
              key={item.id || idx}
              className={`card history-card animate-in`}
              style={{ animationDelay: `${Math.min(idx * 0.05, 0.3)}s` }}
              onClick={() => handleSelect(item)}
            >
              <div className="history-card__header">
                <span className="history-card__date">{formatDate(item.created_at || item.date)}</span>
                <span className="history-card__score">{getAvgScore(item)}</span>
              </div>
              <div className="history-card__platforms">
                {getPlatforms(item).map((p) => (
                  <span key={p} className="badge badge-gold">
                    {PLATFORM_LABELS[p] || p}
                  </span>
                ))}
              </div>
              <div className="history-card__preview">{getPreview(item)}</div>
              <div className="history-card__footer">
                <span>{item.total_tokens || item.tokens || 0} tokens</span>
                <span>{item.total_duration || item.duration
                  ? `${((item.total_duration || item.duration) / 1000).toFixed(1)}s`
                  : ''}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && (
        <DetailModal item={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}

function DetailModal({ item, onClose }) {
  const parseJson = (val) => {
    if (typeof val === 'string') { try { return JSON.parse(val) } catch { return val } }
    return val
  }
  const platformKeys = parseJson(item.platforms) || []
  const finalContent = parseJson(item.final_content) || {}
  const titleOptions = parseJson(item.title_options) || {}
  const reviewScores = parseJson(item.review_scores) || {}

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h3 className="modal__title">生成详情</h3>
          <button className="modal__close" onClick={onClose}>&times;</button>
        </div>

        {item.trend_markdown && (
          <div className="result-block" style={{ marginBottom: 20 }}>
            <div className="result-block__label">原始输入</div>
            <div className="result-block__text" style={{ fontSize: '0.85rem', color: 'var(--cream-dim)' }}>
              {item.trend_markdown}
            </div>
          </div>
        )}

        {platformKeys.length > 0 ? (
          <PlatformTabs platforms={platformKeys}>
            {(active) => {
              const content = finalContent[active] || ''
              const titles = titleOptions[active] || []
              const score = reviewScores[active] || 0
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
                          <div key={i} className="result-title-row">
                            <span className="result-title-text">{typeof t === 'string' ? t : t.title || t.text}</span>
                          </div>
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
                </>
              )
            }}
          </PlatformTabs>
        ) : (
          <div className="empty-state">暂无详细内容</div>
        )}

        {item.total_tokens > 0 && (
          <div className="metrics-row" style={{ marginTop: 20 }}>
            <div className="metric-item">
              <span className="metric-item__label">Token</span>
              <span className="metric-item__value">{item.total_tokens?.toLocaleString()}</span>
            </div>
            {item.total_duration > 0 && (
              <div className="metric-item">
                <span className="metric-item__label">耗时</span>
                <span className="metric-item__value">
                  {(item.total_duration).toFixed(1)}s
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
