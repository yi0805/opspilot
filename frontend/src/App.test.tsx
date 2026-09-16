import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from './App'

const completedResult = {
  answer: 'FW-100 sold 310 units and has 22 units available.', recommendation: 'Prioritize replenishment monitoring for FW-100.',
  evidence: [
    { tool: 'query_sales', arguments: { sku: 'FW-100', start_date: null, end_date: null }, data: [{ sku: 'FW-100', units_sold: 310, revenue: '12396.90', gross_profit: '7281.90' }], source: 'synthetic_business_data' as const },
    { tool: 'query_inventory', arguments: { sku: 'FW-100' }, data: [{ sku: 'FW-100', on_hand: 28, reserved: 6, available_stock: 22, reorder_point: 30, at_or_below_reorder_point: true }], source: 'synthetic_business_data' as const },
  ], status: 'completed' as const,
}
const response = (body: unknown, ok = true, status = 200): Response => ({ ok, status, json: async () => body } as Response)
const installFetch = (implementation: ReturnType<typeof vi.fn>) => vi.stubGlobal('fetch', implementation)
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('renders the initial workspace', () => { render(<App />); expect(screen.getByRole('heading', { name: 'Ask the business. Trace the answer.' })).toBeInTheDocument(); expect(screen.getByLabelText('Business question')).toBeRequired(); expect(screen.getByRole('button', { name: 'Analyze' })).toBeDisabled(); expect(screen.getByRole('button', { name: /How much inventory is available for FW-100/ })).toBeInTheDocument() })
test('an example prompt populates the textarea', () => { render(<App />); const prompt = 'How much inventory is available for FW-100?'; fireEvent.click(screen.getByRole('button', { name: prompt })); expect(screen.getByLabelText('Business question')).toHaveValue(prompt) })
test('prevents blank submissions', () => { const fetchMock = vi.fn(); installFetch(fetchMock); render(<App />); fireEvent.submit(screen.getByRole('button', { name: 'Analyze' }).closest('form')!); expect(fetchMock).not.toHaveBeenCalled() })
test('submits a question and renders answer, recommendation, and evidence', async () => {
  const fetchMock = vi.fn().mockResolvedValue(response(completedResult)); installFetch(fetchMock); render(<App />)
  fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' }))
  await waitFor(() => expect(screen.getByText(completedResult.answer)).toBeInTheDocument())
  expect(fetchMock).toHaveBeenCalledWith('/api/agent/query', expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({ question: 'Check FW-100' }),
    headers: {
      'Content-Type': 'application/json',
      'x-amz-content-sha256': '0b139f2f52525b6e35f841f5310c5a380c3e5e527f5e7c7d53041d313f5fc129',
    },
  })); expect(screen.getByText(completedResult.recommendation)).toBeInTheDocument(); expect(screen.getByRole('heading', { name: 'Sales' })).toBeInTheDocument(); expect(screen.getByRole('heading', { name: 'Inventory' })).toBeInTheDocument(); expect(screen.getByText('310')).toBeInTheDocument(); expect(screen.getByText('22')).toBeInTheDocument()
})
test('shows loading state and disables duplicate submissions', async () => {
  let resolveRequest: (value: Response) => void = () => undefined; const fetchMock = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { resolveRequest = resolve })); installFetch(fetchMock); render(<App />)
  fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); expect(screen.getByRole('button', { name: 'Analyzing…' })).toBeDisabled(); expect(screen.getByRole('button', { name: /How much inventory is available for FW-100/ })).toBeDisabled(); expect(screen.getByText('Analyzing business data…')).toBeInTheDocument(); await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1)); resolveRequest(response(completedResult)); await waitFor(() => expect(screen.queryByText('Analyzing business data…')).not.toBeInTheDocument())
})
test('clears stale results when a question is changed or a follow-up analysis fails', async () => {
  let rejectSecondRequest: (error: Error) => void = () => undefined
  const fetchMock = vi.fn().mockResolvedValueOnce(response(completedResult)).mockImplementationOnce(() => new Promise<Response>((_, reject) => { rejectSecondRequest = reject }))
  installFetch(fetchMock); render(<App />)
  fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Question A' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText(completedResult.answer)).toBeInTheDocument())
  fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Question B' } }); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument(); await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2)); rejectSecondRequest(new Error('offline'))
  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument()); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument()
})
test('selecting an example after a result clears the stale result', async () => {
  installFetch(vi.fn().mockResolvedValue(response(completedResult))); render(<App />)
  fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Question A' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText(completedResult.answer)).toBeInTheDocument())
  const prompt = 'How much inventory is available for FW-100?'; fireEvent.click(screen.getByRole('button', { name: prompt })); expect(screen.getByLabelText('Business question')).toHaveValue(prompt); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument()
})
test('does not render a recommendation panel when recommendation is null', async () => { installFetch(vi.fn().mockResolvedValue(response({ ...completedResult, recommendation: null }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText(completedResult.answer)).toBeInTheDocument()); expect(screen.queryByText('Recommended action')).not.toBeInTheDocument() })
test.each([
  ['tool_error', 'Analysis interrupted'],
  ['tool_limit_reached', 'Analysis limit reached'],
  ['duplicate_tool_call', 'Repeated data request detected'],
] as const)('renders the %s controlled status label with collected evidence', async (status, label) => { installFetch(vi.fn().mockResolvedValue(response({ ...completedResult, answer: 'The analysis did not complete.', recommendation: null, status }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText(label)).toBeInTheDocument()); expect(screen.getByText('The analysis did not complete.')).toBeInTheDocument(); expect(screen.getByRole('heading', { name: 'Sales' })).toBeInTheDocument() })
test('shows a clear message when an evidence record has empty data', async () => { installFetch(vi.fn().mockResolvedValue(response({ ...completedResult, evidence: [{ ...completedResult.evidence[0], data: [] }] }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText('No matching data returned.')).toBeInTheDocument()) })
test('shows a clear message when a completed result has no evidence records', async () => { installFetch(vi.fn().mockResolvedValue(response({ ...completedResult, answer: 'No evidence was returned.', recommendation: null, evidence: [] }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText('No matching data returned.')).toBeInTheDocument()); expect(screen.getByText('0 data sources used')).toBeInTheDocument(); expect(screen.queryByRole('heading', { name: 'Sales' })).not.toBeInTheDocument() })
test('uses the fallback for nested evidence rather than dropping data', async () => { installFetch(vi.fn().mockResolvedValue(response({ ...completedResult, evidence: [{ ...completedResult.evidence[0], data: [{ sku: 'FW-100', metrics: { units_sold: 310 } }] }] }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByText('View returned data')).toBeInTheDocument()); expect(screen.queryByRole('table')).not.toBeInTheDocument(); expect(screen.getByText((_, element) => element?.tagName === 'PRE' && element.textContent?.includes('"units_sold": 310') === true)).toBeInTheDocument() })
test('shows a usable error for backend HTTP failures', async () => { installFetch(vi.fn().mockResolvedValue(response({ detail: 'OPENROUTER_API_KEY is not configured.' }, false, 503))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('OpsPilot could not complete the request.')); expect(screen.getByRole('alert')).toHaveTextContent('OPENROUTER_API_KEY is not configured.'); expect(screen.getByRole('button', { name: 'Analyze' })).toBeEnabled() })
test('shows a safe error for network failures', async () => { installFetch(vi.fn().mockRejectedValue(new Error('offline'))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Check your connection and try again.')) })
test('shows a safe error for an unexpected successful response shape', async () => { installFetch(vi.fn().mockResolvedValue(response({ answer: 'Incomplete payload' }))); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('The service returned an unexpected response. Please try again.')); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument() })
test('shows a safe error for an unreadable response body', async () => { installFetch(vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new SyntaxError('not JSON') } } as unknown as Response)); render(<App />); fireEvent.change(screen.getByLabelText('Business question'), { target: { value: 'Check FW-100' } }); fireEvent.click(screen.getByRole('button', { name: 'Analyze' })); await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('The service returned an unreadable response. Please try again.')); expect(screen.queryByText(completedResult.answer)).not.toBeInTheDocument() })
