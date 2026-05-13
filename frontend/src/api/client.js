const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  generate: (text, platforms, config) => request('/generate', {
    method: 'POST',
    body: JSON.stringify({
      text,
      platforms,
      ...(config && {
        score_threshold: config.scoreThreshold,
        max_cycles: config.maxCycles,
      }),
    }),
  }),
  getHistory: (limit = 20) => request(`/history?limit=${limit}`),
  getGeneration: (id) => request(`/history/${id}`),
  getStats: () => request('/stats'),
  getModels: () => request('/models'),
  switchModel: (name) => request('/models/switch', { method: 'POST', body: JSON.stringify({ name }) }),
  addModel: (model) => request('/models', { method: 'POST', body: JSON.stringify(model) }),
  deleteModel: (name) => request(`/models/${name}`, { method: 'DELETE' }),
  getPlatforms: () => request('/platforms'),
  getConfig: () => request('/config'),
  getPrompts: () => request('/prompts'),
  getPrompt: (name) => request(`/prompts/${name}`),
  updatePrompt: (name, content) => request(`/prompts/${name}`, { method: 'PUT', body: JSON.stringify({ content }) }),
}
