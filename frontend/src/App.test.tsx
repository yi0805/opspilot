import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import App from './App'

test('renders the OpsPilot MVP shell', () => {
  render(<App />)

  expect(screen.getByRole('heading', { name: 'OpsPilot' })).toBeInTheDocument()
  expect(screen.getByText('AI Business Operations Agent')).toBeInTheDocument()
  expect(screen.getByText('MVP in development')).toBeInTheDocument()
})
