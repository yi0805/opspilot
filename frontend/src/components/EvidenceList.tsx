import type { EvidenceRecord, JsonValue } from '../types/agent'

const toolLabels: Record<string, string> = { get_product_details: 'Product details', query_sales: 'Sales', query_inventory: 'Inventory', query_campaigns: 'Campaigns' }
function readableLabel(value: string) { return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function displayValue(value: JsonValue) { if (value === null) return 'Not specified'; if (typeof value === 'boolean') return value ? 'Yes' : 'No'; if (typeof value === 'object') return JSON.stringify(value); return String(value) }
function isScalar(value: JsonValue): value is string | number | boolean | null { return value === null || ['string', 'number', 'boolean'].includes(typeof value) }
function isRecord(value: JsonValue): value is { [key: string]: JsonValue } { return typeof value === 'object' && value !== null && !Array.isArray(value) }

function DataDisplay({ data }: { data: JsonValue }) {
  if ((Array.isArray(data) && data.length === 0) || (isRecord(data) && Object.keys(data).length === 0)) return <p className="empty-data">No matching data returned.</p>
  if (Array.isArray(data) && data.every(isRecord)) {
    const rows = data as { [key: string]: JsonValue }[]
    if (rows.every((row) => Object.values(row).every(isScalar))) {
      const fields = [...new Set(rows.flatMap((row) => Object.keys(row)))]
      if (fields.length > 0) return <div className="table-scroll"><table><thead><tr>{fields.map((field) => <th key={field}>{readableLabel(field)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{fields.map((field) => <td key={field}>{field in row ? displayValue(row[field]) : 'Not specified'}</td>)}</tr>)}</tbody></table></div>
    }
  }
  if (isRecord(data) && Object.values(data).every(isScalar)) return <dl className="data-rows">{Object.entries(data).map(([key, value]) => <div key={key}><dt>{readableLabel(key)}</dt><dd>{displayValue(value)}</dd></div>)}</dl>
  return <details className="json-fallback"><summary>View returned data</summary><pre>{JSON.stringify(data, null, 2)}</pre></details>
}

function Arguments({ arguments: args }: { arguments: EvidenceRecord['arguments'] }) { const specified = Object.entries(args).filter(([, value]) => value !== null); if (specified.length === 0) return null; return <p className="arguments"><span>Scope:</span> {specified.map(([key, value]) => `${readableLabel(key)}: ${displayValue(value)}`).join(' · ')}</p> }
export function EvidenceList({ evidence }: { evidence: EvidenceRecord[] }) { const labels = evidence.map((record) => toolLabels[record.tool] ?? readableLabel(record.tool)); return <section className="evidence-section" aria-labelledby="evidence-title"><div className="evidence-header"><div><p className="eyebrow">Traceability</p><h2 id="evidence-title">Business evidence</h2></div><p className="source-count">{evidence.length} {evidence.length === 1 ? 'data source' : 'data sources'} used</p></div>{evidence.length > 0 && <p className="evidence-summary">Evidence from {labels.join(' + ')}</p>}<div className="evidence-list">{evidence.map((record, index) => <article className="evidence-card" key={`${record.tool}-${index}`}><div className="evidence-card-header"><h3>{toolLabels[record.tool] ?? readableLabel(record.tool)}</h3><span>{readableLabel(record.source)}</span></div><Arguments arguments={record.arguments} /><DataDisplay data={record.data} /></article>)}</div></section> }
