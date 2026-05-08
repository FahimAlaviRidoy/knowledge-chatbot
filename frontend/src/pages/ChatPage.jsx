import { useState, useRef, useEffect } from 'react'
import { Send, RefreshCw, Bot, User, BookOpen, AlertCircle, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { chatApi } from '../services/api'
import './ChatPage.css'

function SourceBadge({ source }) {
  return (
    <div className="source-badge">
      <BookOpen size={10} />
      <span className="source-file">{source.filename}</span>
      <span className="source-score">{Math.round(source.similarity_score * 100)}%</span>
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-bot'}`}>
      <div className="message-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="message-body">
        <div className="message-content">
          {isUser ? (
            <p>{msg.content}</p>
          ) : (
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          )}
        </div>
        {msg.sources?.length > 0 && (
          <div className="message-sources">
            <span className="sources-label">Sources:</span>
            {msg.sources.map((s, i) => <SourceBadge key={i} source={s} />)}
          </div>
        )}
        {msg.in_knowledge_base === false && (
          <div className="out-of-scope">
            <AlertCircle size={12} />
            <span>Not found in knowledge base</span>
          </div>
        )}
        {msg.response_time_ms && (
          <span className="response-time"><Zap size={10} />{msg.response_time_ms}ms</span>
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message message-bot">
      <div className="message-avatar"><Bot size={16} /></div>
      <div className="message-body">
        <div className="typing-indicator">
          <span /><span /><span />
        </div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m **KnowledgeBot**. I can answer questions based on the documents in my knowledge base.\n\nAsk me anything, and I\'ll do my best to find the answer from the uploaded knowledge base.',
      sources: [],
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setLoading(true)
    try {
      const { data } = await chatApi.send(text, sessionId)
      setSessionId(data.session_id)
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          in_knowledge_base: data.in_knowledge_base,
          response_time_ms: data.response_time_ms,
        },
      ])
    } catch (err) {
      toast.error('Failed to get response')
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const clearChat = async () => {
    if (sessionId) {
      try { await chatApi.clearSession(sessionId) } catch {}
    }
    setSessionId(null)
    setMessages([{
      role: 'assistant',
      content: 'Conversation cleared. Start a new session!',
    }])
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-header-left">
          <Bot size={18} />
          <span>KnowledgeBot Chat</span>
          {sessionId && (
            <code className="session-id">Session: {sessionId.slice(0, 8)}</code>
          )}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={clearChat}>
          <RefreshCw size={14} /> New Chat
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-textarea"
            rows={1}
            placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className={`send-btn ${loading ? 'loading' : ''}`}
            onClick={send}
            disabled={!input.trim() || loading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
