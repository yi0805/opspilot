import type { FormEvent } from 'react'

interface QuestionFormProps { question: string; loading: boolean; onQuestionChange: (question: string) => void; onSubmit: () => void }

export function QuestionForm({ question, loading, onQuestionChange, onSubmit }: QuestionFormProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); onSubmit() }
  return <form className="question-form" onSubmit={submit}>
    <div className="form-heading"><label htmlFor="business-question">Business question</label><span>{question.length}/500</span></div>
    <textarea id="business-question" value={question} maxLength={500} required disabled={loading} onChange={(event) => onQuestionChange(event.target.value)} placeholder="Compare FW-100 sales and inventory. Is there a replenishment risk and what should we do?" rows={4} />
    <div className="form-actions"><p>OpsPilot uses synthetic sales, inventory, product, and campaign data.</p><button type="submit" disabled={loading || !question.trim()}>{loading ? 'Analyzing…' : 'Analyze'}</button></div>
  </form>
}
