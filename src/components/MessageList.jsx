import React from 'react'

function MessageList({ messages, loading, error }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-gray-850 border border-gray-700 rounded-lg mb-4">
        <div className="w-8 h-8 border-4 border-gray-600 border-t-primary-300 rounded-full animate-spin mb-4"></div>
        <p className="text-gray-400">Loading messages...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-900/20 border border-red-500 rounded-lg mb-4">
        <div className="text-3xl mb-2">⚠️</div>
        <p className="text-red-400 text-center">{error}</p>
      </div>
    )
  }

  if (!messages || messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-gray-850 border border-gray-700 rounded-lg mb-4">
        <div className="text-5xl mb-4 opacity-50">💬</div>
        <h3 className="text-xl font-semibold text-white mb-2">No messages yet</h3>
        <p className="text-gray-400 text-center">Start the conversation by sending your first message below.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 p-4 bg-gray-850 border border-gray-700 rounded-lg mb-4 max-h-96 overflow-y-auto">
      {messages.map((message, index) => (
        <MessageItem key={index} message={message} />
      ))}
    </div>
  )
}

function MessageItem({ message }) {
  const isUser = message.role === 'user'
  const timestamp = new Date(message.timestamp).toLocaleString()

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-primary-600 text-white' 
          : 'bg-gray-700 text-gray-100 border border-gray-600'
      }`}>
        <div className="flex items-center justify-between mb-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-sm">
              {isUser ? '👤' : '🤖'}
            </span>
            <span className={`font-medium ${isUser ? 'text-primary-100' : 'text-gray-300'}`}>
              {isUser ? 'You' : 'Agent'}
            </span>
          </div>
          <div className={`text-xs ${isUser ? 'text-primary-200' : 'text-gray-400'}`}>
            {timestamp}
          </div>
        </div>
        <div className="text-sm leading-relaxed">
          {typeof message.content === 'string' ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : Array.isArray(message.content) ? (
            message.content.map((item, idx) => (
              <div key={idx} className="mb-2 last:mb-0">
                {item.text && <p className="whitespace-pre-wrap">{item.text}</p>}
                {item.image && (
                  <img 
                    src={item.image} 
                    alt="Message attachment" 
                    className="max-w-full h-auto rounded mt-2"
                  />
                )}
              </div>
            ))
          ) : (
            <p className="whitespace-pre-wrap">{JSON.stringify(message.content)}</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default MessageList