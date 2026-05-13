import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    Promise.all([api.getStats(), api.getHistory(5)])
      .then(([statsData, historyData]) => {
        if (cancelled) return
        setStats(statsData)
        setRecent(Array.isArray(historyData) ? historyData : historyData.items || [])
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const PLATFORM_LABELS = {
    xiaohongshu: '小红书',
    wechat: '微信公众号',
    douyin: '抖音',
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
    const text = (item.trend_markdown || '').replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim()
    const maxLen = 50
    if (text.length <= maxLen) return text
    return text.slice(0, maxLen) + '...'
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
          <h1>数据概览</h1>
          <p>查看使用统计和最近生成</p>
        </div>
        <div className="empty-state">
          <div className="spinner" />
          <span>加载中...</span>
        </div>
      </div>
    )
  }

  const statCards = [
    { label: '总生成次数', value: stats?.total_generations ?? 0, unit: '次' },
    { label: '总消耗 Token', value: stats?.total_tokens ?? 0, unit: '' },
    { label: '平均耗时', value: stats?.avg_duration ? stats.avg_duration.toFixed(1) : '0', unit: 's' },
    { label: '平均评分', value: stats?.avg_score ?? '-', unit: '' },
  ]

  return (
    <div>
      <div className="page-header animate-in">
        <h1>数据概览</h1>
        <p>ContentForge 使用统计</p>
      </div>

      {error && <div className="error-banner animate-in">{error}</div>}

      <div className="stats-row">
        {statCards.map((s) => (
          <div key={s.label} className="card stat-card">
            <div className="stat-value">
              {s.value}
              {s.unit && <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--cream-dim)', marginLeft: 4 }}>{s.unit}</span>}
            </div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="recent-header animate-in-delay-1">
        <h2>最近生成</h2>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/history')}>
          查看全部 &rarr;
        </button>
      </div>

      {recent.length === 0 ? (
        <div className="empty-state animate-in-delay-2">
          <span style={{ fontSize: '2rem' }}>&#128640;</span>
          <span>还没有生成记录，开始创作吧</span>
        </div>
      ) : (
        <div className="recent-list">
          {recent.map((item, idx) => (
            <div
              key={item.id || idx}
              className="recent-item animate-in"
              style={{ animationDelay: `${0.15 + idx * 0.05}s` }}
              onClick={() => navigate('/history')}
            >
              <div className="recent-item__left">
                <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                  {getPlatforms(item).map((p) => (
                    <span key={p} className="badge badge-gold">
                      {PLATFORM_LABELS[p] || p}
                    </span>
                  ))}
                </div>
                <span className="recent-item__preview">{getPreview(item)}</span>
              </div>
              <div className="recent-item__right">
                <span className="recent-item__score">{getAvgScore(item)}</span>
                <span className="recent-item__meta">
                  {item.total_tokens || item.tokens || 0} tk
                </span>
                <span className="recent-item__meta">
                  {formatDate(item.created_at || item.date)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
