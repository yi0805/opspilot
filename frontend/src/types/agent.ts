export type JsonPrimitive = string | number | boolean | null
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue }

export type AgentStatus =
  | 'completed'
  | 'tool_error'
  | 'tool_limit_reached'
  | 'duplicate_tool_call'

export interface EvidenceRecord {
  tool: string
  arguments: { [key: string]: JsonValue }
  data: JsonValue
  source: 'synthetic_business_data'
}

export interface AgentQueryResult {
  answer: string
  recommendation: string | null
  evidence: EvidenceRecord[]
  status: AgentStatus
}
