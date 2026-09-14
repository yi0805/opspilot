import { useState } from 'react'
import { AgentApiError, queryAgent } from './api/agent'
import { ExamplePrompts } from './components/ExamplePrompts'
import { QuestionForm } from './components/QuestionForm'
import { ResultPanel } from './components/ResultPanel'
import './App.css'
import type { AgentQueryResult } from './types/agent'

function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AgentQueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const submitQuestion = async () => {
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || loading) return
    setLoading(true)
    setError(null)
    try {
      setResult(await queryAgent(trimmedQuestion))
    } catch (requestError) {
      setError(requestError instanceof AgentApiError ? requestError.message : 'Please try again.')
    } finally {
      setLoading(false)
    }
  }
  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#workspace" aria-label="OpsPilot workspace">OpsPilot</a>
        <div className="product-meta"><span>Business Operations Intelligence</span><span className="demo-label">Synthetic demo data</span></div>
      </header>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Operational intelligence</p><h1 id="page-title">Ask the business. Trace the answer.</h1>
        <p>Combine sales, inventory, product, and campaign data into evidence-backed operational recommendations.</p>
      </section>
      <section className="workspace" id="workspace" aria-labelledby="workspace-title">
        <div className="section-heading"><p className="eyebrow">Question workspace</p><h2 id="workspace-title">What do you need to know?</h2></div>
        <QuestionForm question={question} loading={loading} onQuestionChange={setQuestion} onSubmit={submitQuestion} />
        {loading && <div className="loading-message" role="status"><span className="spinner" aria-hidden="true" />Analyzing business data…</div>}
        {error && <div className="error-panel" role="alert"><strong>OpsPilot could not complete the request.</strong><span>{error}</span></div>}
      </section>
      <ExamplePrompts onSelect={setQuestion} />
      {result && <ResultPanel result={result} />}
    </main>
  )
}

export default App
