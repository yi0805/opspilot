import type { AgentQueryResult, EvidenceRecord, JsonValue } from '../types/agent'

export class AgentApiError extends Error {}

function isJsonValue(value: unknown): value is JsonValue {
  if (value === null || ['string', 'number', 'boolean'].includes(typeof value)) return true
  if (Array.isArray(value)) return value.every(isJsonValue)
  return typeof value === 'object' && Object.values(value).every(isJsonValue)
}

function isEvidenceRecord(value: unknown): value is EvidenceRecord {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return typeof record.tool === 'string' && typeof record.arguments === 'object' && record.arguments !== null && !Array.isArray(record.arguments) && isJsonValue(record.data) && record.source === 'synthetic_business_data'
}

function isAgentQueryResult(value: unknown): value is AgentQueryResult {
  if (typeof value !== 'object' || value === null) return false
  const result = value as Record<string, unknown>
  return typeof result.answer === 'string' && (typeof result.recommendation === 'string' || result.recommendation === null) && Array.isArray(result.evidence) && result.evidence.every(isEvidenceRecord) && ['completed', 'tool_error', 'tool_limit_reached', 'duplicate_tool_call'].includes(String(result.status))
}

function errorDetail(value: unknown): string | null {
  if (typeof value !== 'object' || value === null) return null
  const detail = (value as Record<string, unknown>).detail
  return typeof detail === 'string' && detail.trim() ? detail : null
}

export async function queryAgent(question: string): Promise<AgentQueryResult> {
  let response: Response
  try {
    response = await fetch('/api/agent/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) })
  } catch {
    throw new AgentApiError('Check your connection and try again.')
  }
  let body: unknown
  try { body = await response.json() } catch { throw new AgentApiError('The service returned an unreadable response. Please try again.') }
  if (!response.ok) throw new AgentApiError(errorDetail(body) ?? 'The service could not process this request.')
  if (!isAgentQueryResult(body)) throw new AgentApiError('The service returned an unexpected response. Please try again.')
  return body
}
