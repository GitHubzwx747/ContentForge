import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

export default function Models() {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const loadModels = useCallback(() => {
    setLoading(true)
    api.getModels()
      .then((data) => setModels(Array.isArray(data) ? data : data.models || []))
      .catch((err) => setError(err.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { loadModels() }, [loadModels])

  const handleSwitch = async (name) => {
    try {
      await api.switchModel(name)
      loadModels()
    } catch (err) {
      setError(err.message || '切换失败')
    }
  }

  const handleDelete = async () => {
    if (!confirmDelete) return
    try {
      await api.deleteModel(confirmDelete)
      setConfirmDelete(null)
      loadModels()
    } catch (err) {
      setError(err.message || '删除失败')
      setConfirmDelete(null)
    }
  }

  const handleAdd = async (model) => {
    try {
      await api.addModel(model)
      setShowForm(false)
      loadModels()
    } catch (err) {
      setError(err.message || '添加失败')
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1>模型管理</h1>
          <p>管理可用的 AI 模型</p>
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
        <h1>模型管理</h1>
        <p>管理可用的 AI 模型，切换当前使用的模型</p>
      </div>

      {error && <div className="error-banner animate-in">{error}</div>}

      <div className="models-grid">
        {models.map((model, idx) => (
          <div
            key={model.name || idx}
            className={`card model-card animate-in ${model.active ? 'model-card--active' : ''}`}
            style={{ animationDelay: `${Math.min(idx * 0.05, 0.3)}s` }}
            onClick={() => !model.active && handleSwitch(model.name)}
          >
            {model.active && (
              <span className="model-card__badge badge badge-gold">当前</span>
            )}
            <div className="model-card__name">{model.name}</div>
            <div className="model-card__source">{model.source || model.provider || ''}</div>
            {model.description && (
              <div className="model-card__details">{model.description}</div>
            )}
            {model.base_url && (
              <div className="model-card__details" style={{ marginTop: 4 }}>
                {model.base_url}
              </div>
            )}
            <div className="model-card__actions">
              {!model.active && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={(e) => { e.stopPropagation(); handleSwitch(model.name) }}
                >
                  设为当前
                </button>
              )}
              {!model.active && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={(e) => { e.stopPropagation(); setConfirmDelete(model.name) }}
                >
                  删除
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {!showForm && (
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(true)}
        >
          + 添加模型
        </button>
      )}

      {showForm && (
        <AddModelForm
          onSubmit={handleAdd}
          onCancel={() => setShowForm(false)}
        />
      )}

      {confirmDelete && (
        <div className="confirm-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="confirm-box" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-box__text">
              确定要删除模型 <strong>{confirmDelete}</strong> 吗？此操作不可撤销。
            </div>
            <div className="confirm-box__actions">
              <button className="btn btn-secondary btn-sm" onClick={() => setConfirmDelete(null)}>
                取消
              </button>
              <button className="btn btn-danger btn-sm" onClick={handleDelete}>
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AddModelForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({
    name: '',
    source: '',
    base_url: '',
    api_key: '',
    description: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setSubmitting(true)
    await onSubmit(form)
    setSubmitting(false)
  }

  return (
    <form className="add-model-form card animate-in" onSubmit={handleSubmit}>
      <div className="card-title" style={{ marginBottom: 20 }}>添加模型</div>

      <div className="form-field">
        <label className="form-field__label">模型名称 *</label>
        <input
          className="form-field__input"
          placeholder="例如 gpt-4o"
          value={form.name}
          onChange={update('name')}
          required
        />
      </div>

      <div className="form-field">
        <label className="form-field__label">来源 / 供应商</label>
        <input
          className="form-field__input"
          placeholder="例如 openai, deepseek"
          value={form.source}
          onChange={update('source')}
        />
      </div>

      <div className="form-field">
        <label className="form-field__label">API Base URL</label>
        <input
          className="form-field__input"
          placeholder="例如 https://api.openai.com/v1"
          value={form.base_url}
          onChange={update('base_url')}
        />
      </div>

      <div className="form-field">
        <label className="form-field__label">API Key</label>
        <input
          className="form-field__input"
          type="password"
          placeholder="sk-..."
          value={form.api_key}
          onChange={update('api_key')}
        />
      </div>

      <div className="form-field">
        <label className="form-field__label">描述</label>
        <input
          className="form-field__input"
          placeholder="可选描述"
          value={form.description}
          onChange={update('description')}
        />
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary btn-sm" disabled={submitting || !form.name.trim()}>
          {submitting ? '添加中...' : '确认添加'}
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={onCancel}>
          取消
        </button>
      </div>
    </form>
  )
}
