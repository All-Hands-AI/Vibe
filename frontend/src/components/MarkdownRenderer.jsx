import { marked } from 'marked'
import DOMPurify from 'dompurify'
import PropTypes from 'prop-types'
import './MarkdownRenderer.css'

// Configure marked options for security and consistency
marked.setOptions({
  breaks: true, // Convert line breaks to <br>
  gfm: true, // Enable GitHub Flavored Markdown
  headerIds: false, // Disable header IDs for security
  mangle: false, // Don't mangle email addresses
  pedantic: false, // Don't be pedantic about markdown
  sanitize: false // We'll handle sanitization with DOMPurify
})

function MarkdownRenderer({ content, className = '' }) {
  // Parse markdown and sanitize HTML
  const renderMarkdown = (text) => {
    try {
      // First, parse the markdown
      const rawHtml = marked(text)
      
      // Then sanitize the HTML to prevent XSS attacks
      const cleanHtml = DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'ul', 'ol', 'li',
          'blockquote',
          'code', 'pre',
          'a',
          'img',
          'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ],
        ALLOWED_ATTR: [
          'href', 'title', 'alt', 'src', 'width', 'height',
          'class', 'id'
        ],
        ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp):|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i
      })
      
      return cleanHtml
    } catch (error) {
      console.error('Error rendering markdown:', error)
      // Fallback to plain text if markdown parsing fails
      return DOMPurify.sanitize(text)
    }
  }

  return (
    <div 
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
      style={{
        // Custom styles for markdown elements
        '--markdown-color': 'inherit',
        '--markdown-link-color': '#00ff88',
        '--markdown-code-bg': 'rgba(0, 0, 0, 0.5)',
        '--markdown-blockquote-border': '#666'
      }}
    />
  )
}

MarkdownRenderer.propTypes = {
  content: PropTypes.string.isRequired,
  className: PropTypes.string
}

export default MarkdownRenderer