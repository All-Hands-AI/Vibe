# Conversation Interface Implementation

This document describes the implementation of the conversation interface for OpenVibe, which allows users to send messages to AI agents and view conversation history with real-time updates.

## 🎯 Overview

The conversation interface provides a complete chat experience with:
- **Message Display**: Shows conversation history with user and agent messages
- **Message Sending**: Allows users to send messages to the AI agent
- **Real-time Updates**: Polls for new messages and events periodically
- **Live Controls**: Enable/disable polling and refresh conversation data
- **Responsive Design**: Built with Tailwind CSS for all screen sizes

## 🏗️ Architecture

### Components

#### **MessageList Component** (`src/components/MessageList.jsx`)
Displays the conversation history with different message types using Tailwind CSS:

```jsx
<MessageList 
  messages={messages} 
  loading={loading} 
  error={error}
/>
```

**Features:**
- User messages: Right-aligned with blue background (`bg-primary-600`)
- Agent messages: Left-aligned with gray background (`bg-gray-700`)
- Loading, error, and empty states
- Auto-scrolling message container with Tailwind scrollbar styling
- Responsive design with `max-w-xs lg:max-w-md` for message bubbles

#### **MessageInput Component** (`src/components/MessageInput.jsx`)
Provides message input and sending functionality with Tailwind styling:

```jsx
<MessageInput 
  onSendMessage={sendMessage}
  disabled={disabled}
  placeholder="Type your message..."
/>
```

**Features:**
- Auto-resizing textarea with Tailwind classes
- Send button with hover effects and loading spinner
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Input validation and trimming
- Tailwind-based responsive design

#### **useConversation Hook** (`src/hooks/useConversation.js`)
Custom hook that manages conversation state and API interactions:

```jsx
const {
  messages,
  events,
  conversation,
  loading,
  error,
  sending,
  sendMessage,
  refresh,
  pollingEnabled,
  setPollingEnabled,
  isPolling
} = useConversation(projectId, conversationId)
```

**Features:**
- Loads conversation details and messages
- Sends messages to the API
- Polls for new events and messages every 5 seconds
- Handles page visibility changes (pauses when tab is inactive)
- Manages loading and error states

### Updated ConversationDetail Page

The main conversation page (`src/pages/ConversationDetail.jsx`) now includes:
- Message interface with MessageList and MessageInput
- Live update controls with Tailwind button styling
- Refresh button for manual updates
- Real-time status indicators
- Enhanced conversation metadata display

## 🎨 Tailwind CSS Styling

### Design System

The interface uses a consistent Tailwind-based design system:

**Colors:**
- Background: `bg-gray-900` (main), `bg-gray-850` (cards), `bg-gray-800` (inputs)
- Text: `text-white` (primary), `text-gray-300` (secondary), `text-gray-400` (muted)
- Primary: `bg-primary-600`, `text-primary-300`, `border-primary-500`
- Borders: `border-gray-700`, `border-gray-600`

**Message Styling:**
```jsx
// User messages
className="bg-primary-600 text-white max-w-xs lg:max-w-md"

// Agent messages  
className="bg-gray-700 text-gray-100 border border-gray-600 max-w-xs lg:max-w-md"
```

**Interactive Elements:**
```jsx
// Buttons
className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:opacity-50 text-white border border-gray-600 rounded-lg transition-colors duration-200"

// Input areas
className="bg-gray-800 border border-gray-600 rounded-lg p-3 focus-within:border-primary-500 transition-colors"
```

### Responsive Design

The interface adapts using Tailwind's responsive utilities:
- **Mobile**: Single column layout, full-width controls
- **Desktop**: Optimized spacing with `lg:` prefixes
- **Tablet**: Balanced layout with appropriate touch targets

## 🔄 API Integration

### Endpoints Used

#### Load Conversation
```http
GET /projects/{projectId}/conversations/{conversationId}
X-User-UUID: {userUUID}
```

#### Send Message
```http
POST /projects/{projectId}/conversations/{conversationId}/messages
X-User-UUID: {userUUID}
Content-Type: application/json

{
  "message": "User message content"
}
```

#### Get Events
```http
GET /projects/{projectId}/conversations/{conversationId}/events
X-User-UUID: {userUUID}
```

### Message Format

Messages follow this structure:
```javascript
{
  role: 'user' | 'agent',
  content: string | Array<{text?: string, image?: string}>,
  timestamp: string // ISO 8601 format
}
```

## 🔄 Real-time Updates

### Polling Mechanism

The interface polls for updates every 5 seconds when:
- The page is visible (not in background tab)
- Polling is enabled (not paused by user)
- No errors are present
- Initial loading is complete

### Event Detection

The system detects new activity by:
1. Polling the events endpoint
2. Comparing event count with previous poll
3. Reloading conversation data when new events are detected
4. Updating the message list automatically

### Page Visibility Handling

Polling automatically pauses when:
- User switches to another tab (`document.hidden`)
- Browser window is minimized
- User explicitly pauses updates

## 🧪 Testing

### Component Tests

**MessageList Tests** (`src/components/MessageList.test.jsx`):
- Loading state rendering with Tailwind spinner
- Error state handling with red styling
- Empty state display
- Message rendering with different content types
- User vs agent message styling verification

**MessageInput Tests** (`src/components/MessageInput.test.jsx`):
- Form submission handling
- Keyboard shortcuts (Enter, Shift+Enter)
- Input validation and trimming
- Disabled state behavior
- Message clearing after send

### Integration Testing

To test the complete interface:

1. **Setup**: Ensure backend is running with OpenHands SDK
2. **Create Conversation**: Use the project interface to create a conversation
3. **Send Messages**: Test message sending and receiving
4. **Polling**: Verify real-time updates work correctly
5. **Error Handling**: Test behavior when API is unavailable

## 🚀 Usage Examples

### Basic Usage

```jsx
// In a React component
import { useConversation } from '../hooks/useConversation'
import MessageList from '../components/MessageList'
import MessageInput from '../components/MessageInput'

function MyConversation({ projectId, conversationId }) {
  const {
    messages,
    loading,
    error,
    sendMessage,
    pollingEnabled,
    setPollingEnabled
  } = useConversation(projectId, conversationId)

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto p-8">
        <MessageList messages={messages} loading={loading} error={error} />
        <MessageInput onSendMessage={sendMessage} disabled={loading || error} />
        <button 
          onClick={() => setPollingEnabled(!pollingEnabled)}
          className="mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
        >
          {pollingEnabled ? 'Pause' : 'Resume'} Updates
        </button>
      </div>
    </div>
  )
}
```

## 🔧 Configuration

### Polling Interval

The polling interval is set to 5 seconds by default. To change it, modify the `useConversation` hook:

```javascript
// In useConversation.js
pollingIntervalRef.current = setInterval(() => {
  if (pollingEnabled) {
    loadEvents()
  }
}, 3000) // Change to 3 seconds
```

### Tailwind Customization

The interface uses Tailwind's default configuration. To customize colors:

```javascript
// In tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          300: '#your-color',
          400: '#your-color',
          500: '#your-color',
          600: '#your-color',
          700: '#your-color',
        },
        gray: {
          850: '#your-custom-gray',
        }
      }
    }
  }
}
```

## 🐛 Error Handling

### Common Error Scenarios

1. **API Unavailable**: Shows error message with red Tailwind styling
2. **Network Issues**: Graceful degradation with offline indicators
3. **Invalid Messages**: Input validation prevents empty/invalid messages
4. **Authentication**: Proper error messages for auth failures

### Error Recovery

- **Automatic Retry**: Polling resumes automatically when errors resolve
- **Manual Refresh**: Users can manually refresh conversation data
- **Graceful Degradation**: Interface remains functional even with partial failures

## 🔮 Future Enhancements

### Planned Features

1. **Message Search**: Search through conversation history
2. **File Attachments**: Support for file uploads and sharing
3. **Message Reactions**: Like/dislike messages with Tailwind hover effects
4. **Typing Indicators**: Show when agent is responding
5. **Message Threading**: Reply to specific messages
6. **Export Conversations**: Download conversation history

### Performance Optimizations

1. **Virtual Scrolling**: For very long conversations
2. **Message Caching**: Cache messages locally
3. **Optimistic Updates**: Show messages immediately before API confirmation
4. **WebSocket Support**: Replace polling with real-time WebSocket connections

## 📱 Mobile Considerations

### Tailwind Mobile-First Design
- Uses `sm:`, `md:`, `lg:` breakpoints for responsive behavior
- Touch-friendly button sizes with adequate padding
- Optimized text sizes for mobile readability

### Performance
- Efficient Tailwind CSS bundle with purging
- Reduced polling frequency on mobile networks
- Optimized rendering for mobile devices

## 🔐 Security Considerations

### Data Protection
- User UUID authentication for all API calls
- Message content validation and sanitization
- Secure transmission of sensitive data

### Privacy
- No message content stored in browser localStorage
- Automatic cleanup of sensitive data
- Respect for user privacy preferences

---

This conversation interface provides a modern, responsive chat experience using Tailwind CSS while maintaining good performance, user experience, and extensibility for future enhancements.