/**
 * ATLAS-OPS API Client
 * Central fetch wrapper for all backend API calls.
 */

const API_BASE = '/v1'

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Backend unavailable. Ensure the API is running on port 8000.')
    }
    throw err
  }
}

export const api = {
  // Health
  health: () => request('/health'),

  // Transactions
  processTransaction: (data) =>
    request('/transaction/process', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Gateway Health
  getGatewayHealth: () => request('/gateways/health'),

  // ML Status
  getMLStatus: () => request('/ml/status'),

  // Explain
  explainTransaction: (txnId) => request(`/transaction/${txnId}/explain`),

  // Simulate Outage
  simulateOutage: (data, adminKey) =>
    request('/simulate/outage', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'X-Admin-Key': adminKey },
    }),

  clearOutage: (gateway, adminKey) =>
    request(`/simulate/outage/${gateway}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Key': adminKey },
    }),
}

/**
 * Start an SSE connection for the live pipeline.
 * Returns a function to abort the connection.
 */
export function connectPipelineSSE(transactionData, onEvent, onError, onComplete) {
  const controller = new AbortController()

  fetch(`${API_BASE}/transaction/process-live`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(transactionData),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Pipeline request failed' }))
        onError(new Error(err.detail || `HTTP ${response.status}`))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              onEvent(event)
            } catch {
              // skip malformed events
            }
          }
        }
      }

      onComplete?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err)
      }
    })

  return () => controller.abort()
}

export default api
