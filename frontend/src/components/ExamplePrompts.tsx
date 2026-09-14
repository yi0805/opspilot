const prompts = [
  'Compare FW-100 sales and inventory. Is there a replenishment risk and what should we do?',
  'Which product appears overstocked relative to demand, and what action would you recommend?',
  'How is the Turbo Video Launch campaign performing, and should we continue spending on it?',
  'How much inventory is available for FW-100?',
]

export function ExamplePrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  return <section className="examples" aria-labelledby="example-prompts-title"><div className="section-heading"><p className="eyebrow">Start with a signal</p><h2 id="example-prompts-title">Example questions</h2></div><div className="prompt-list">{prompts.map((prompt) => <button key={prompt} type="button" className="prompt-button" onClick={() => onSelect(prompt)}>{prompt}</button>)}</div></section>
}
