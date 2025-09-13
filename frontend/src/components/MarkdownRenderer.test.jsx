import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MarkdownRenderer from './MarkdownRenderer'

describe('MarkdownRenderer', () => {
  it('renders plain text correctly', () => {
    render(<MarkdownRenderer content="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders markdown bold text', () => {
    render(<MarkdownRenderer content="**bold text**" />)
    const boldElement = screen.getByText('bold text')
    expect(boldElement.tagName).toBe('STRONG')
  })

  it('renders markdown italic text', () => {
    render(<MarkdownRenderer content="*italic text*" />)
    const italicElement = screen.getByText('italic text')
    expect(italicElement.tagName).toBe('EM')
  })

  it('renders markdown links', () => {
    render(<MarkdownRenderer content="[OpenVibe](https://openvibe.dev)" />)
    const linkElement = screen.getByRole('link', { name: 'OpenVibe' })
    expect(linkElement).toHaveAttribute('href', 'https://openvibe.dev')
  })

  it('renders inline code', () => {
    render(<MarkdownRenderer content="Use `console.log()` for debugging" />)
    const codeElement = screen.getByText('console.log()')
    expect(codeElement.tagName).toBe('CODE')
  })

  it('renders markdown headers', () => {
    render(<MarkdownRenderer content="# Main Title" />)
    const headerElement = screen.getByText('Main Title')
    expect(headerElement.tagName).toBe('H1')
  })

  it('sanitizes dangerous HTML', () => {
    render(<MarkdownRenderer content="<script>alert('xss')</script>Safe content" />)
    expect(screen.getByText('Safe content')).toBeInTheDocument()
    expect(screen.queryByText("alert('xss')")).not.toBeInTheDocument()
  })

  it('renders basic markdown content', () => {
    const { container } = render(<MarkdownRenderer content="This is **bold** and *italic* text" />)
    expect(container.querySelector('strong')).toBeInTheDocument()
    expect(container.querySelector('em')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<MarkdownRenderer content="Test" className="custom-class" />)
    const markdownDiv = container.querySelector('.markdown-content')
    expect(markdownDiv).toHaveClass('custom-class')
  })
})