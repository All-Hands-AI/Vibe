import PropTypes from 'prop-types'
import MarkdownRenderer from './MarkdownRenderer'

function MessageList({ messages, userUuid, scrollContainerRef, onScroll, messagesEndRef }) {
  // No auto-scroll here - handled by parent ChatWindow component

  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })
    } catch {
      return 'Invalid time'
    }
  }

  const formatDate = (timestamp) => {
    try {
      const date = new Date(timestamp)
      const today = new Date()
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)

      if (date.toDateString() === today.toDateString()) {
        return 'Today'
      } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday'
      } else {
        return date.toLocaleDateString([], { 
          month: 'short', 
          day: 'numeric',
          year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
        })
      }
    } catch {
      return 'Invalid date'
    }
  }

  const isOwnMessage = (message) => {
    return message.created_by === userUuid
  }

  const getMessageTypeIcon = (message) => {
    // For special message types, show the type-specific icon
    switch (message.type) {
      case 'file':
        return '📎'
      case 'image':
        return '🖼️'
      case 'code':
        return '💻'
      default:
        // For regular messages, show person for user, robot for agent
        return isOwnMessage(message) ? '👤' : '🤖'
    }
  }

  // Group messages by date
  const groupedMessages = messages.reduce((groups, message) => {
    const date = formatDate(message.created_at)
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(message)
    return groups
  }, {})

  if (messages.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">💬</div>
          <h3 className="text-xl font-semibold text-cyber-muted mb-2">No messages yet</h3>
          <p className="text-cyber-muted">Start the conversation by sending a message below.</p>
        </div>
      </div>
    )
  }

  return (
    <div 
      ref={scrollContainerRef}
      className="h-full overflow-y-auto p-4 space-y-4"
      onScroll={onScroll}
    >
      {Object.entries(groupedMessages).map(([date, dateMessages]) => (
        <div key={date}>
          {/* Date Separator */}
          <div className="flex items-center justify-center my-4">
            <div className="flex-1 border-t border-gray-700"></div>
            <span className="px-3 text-xs text-cyber-muted font-mono bg-black">
              {date}
            </span>
            <div className="flex-1 border-t border-gray-700"></div>
          </div>

          {/* Messages for this date */}
          <div className="space-y-3">
            {dateMessages.map((message) => (
              <div
                key={message.id}
                className={`flex ${isOwnMessage(message) ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    isOwnMessage(message)
                      ? 'bg-neon-green/20 text-cyber-text border border-neon-green/30'
                      : 'bg-gray-800 text-cyber-text border border-gray-600'
                  }`}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs">
                        {getMessageTypeIcon(message)}
                      </span>
                      <span className="text-xs text-cyber-muted font-mono">
                        {isOwnMessage(message) ? 'You' : 'Agent'}
                      </span>
                    </div>
                    <span className="text-xs text-cyber-muted font-mono">
                      {formatTime(message.created_at)}
                    </span>
                  </div>

                  {/* Message Content */}
                  <div className="text-sm">
                    {message.type === 'code' ? (
                      <pre className="bg-black/50 p-2 rounded text-xs font-mono overflow-x-auto">
                        <code>{message.content}</code>
                      </pre>
                    ) : message.type === 'file' ? (
                      <div className="flex items-center space-x-2">
                        <span>📎</span>
                        <span className="font-mono text-xs">
                          {message.metadata?.filename || 'File attachment'}
                        </span>
                      </div>
                    ) : (
                      <MarkdownRenderer 
                        content={message.content}
                        className="break-words"
                      />
                    )}
                  </div>

                  {/* Message Metadata */}
                  {message.metadata && Object.keys(message.metadata).length > 0 && (
                    <div className={`mt-2 pt-2 ${isOwnMessage(message) ? 'border-t border-gray-600/50' : ''}`}>
                      <div className="text-xs text-cyber-muted font-mono">
                        {message.metadata.filename && (
                          <div>File: {message.metadata.filename}</div>
                        )}
                        {message.metadata.size && (
                          <div>Size: {message.metadata.size}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      {/* Scroll anchor - placed at the very end of messages */}
      <div ref={messagesEndRef} style={{ height: '1px' }} />
    </div>
  )
}

MessageList.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      content: PropTypes.string.isRequired,
      created_at: PropTypes.string.isRequired,
      created_by: PropTypes.string.isRequired,
      type: PropTypes.string,
      metadata: PropTypes.object
    })
  ).isRequired,
  userUuid: PropTypes.string.isRequired,
  scrollContainerRef: PropTypes.object,
  onScroll: PropTypes.func,
  messagesEndRef: PropTypes.object
}

export default MessageList
