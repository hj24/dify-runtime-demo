import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, Bot, User, Loader2, Code, MessageSquare, Save } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'editor'
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  // Editor State
  const [dslContent, setDslContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState('')

  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Load conversation ID
    const storedId = localStorage.getItem('dify_conversation_id')
    if (storedId) {
      setConversationId(storedId)
      fetchHistory(storedId)
    }
    // Load DSL
    fetchDSL()
  }, [])

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom()
    }
  }, [messages, activeTab])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const fetchHistory = async (id) => {
    try {
      const res = await axios.get(`${API_BASE}/chat/history/${id}`)
      setMessages(res.data)
    } catch (err) {
      console.error("Failed to fetch history", err)
      // If history fetch fails (e.g. 404), maybe clear ID
      if (err.response && err.response.status === 404) {
        localStorage.removeItem('dify_conversation_id')
        setConversationId(null)
      }
    }
  }

  const fetchDSL = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dsl/content`)
      setDslContent(res.data.content)
    } catch (err) {
      console.error("Failed to fetch DSL", err)
    }
  }

  const saveDSL = async () => {
    setSaving(true)
    setSaveStatus('Saving...')
    try {
      await axios.post(`${API_BASE}/dsl/content`, { content: dslContent })
      setSaveStatus('Saved & Reloaded!')
      setTimeout(() => setSaveStatus(''), 3000)
    } catch (err) {
      console.error("Failed to save DSL", err)
      setSaveStatus('Error saving DSL')
    } finally {
      setSaving(false)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await axios.post(`${API_BASE}/chat/send`, {
        query: userMsg.content,
        conversation_id: conversationId
      })

      const data = res.data
      if (!conversationId) {
        setConversationId(data.conversation_id)
        localStorage.setItem('dify_conversation_id', data.conversation_id)
      }

      const botMsg = { role: 'assistant', content: data.response }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', content: "Error: Failed to send message. Please check backend connection." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="header">
        <div className="avatar" style={{ backgroundColor: 'transparent' }}>
          <Bot size={28} color="#3b82f6" />
        </div>
        <h1>Dify Runtime Demo</h1>
        <div style={{ flex: 1 }} />
        <div className="tabs" style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setActiveTab('chat')}
            style={{ backgroundColor: activeTab === 'chat' ? 'var(--primary)' : 'transparent', border: activeTab === 'chat' ? 'none' : '1px solid var(--border-color)' }}
          >
            <MessageSquare size={16} /> Chat
          </button>
          <button
            onClick={() => setActiveTab('editor')}
            style={{ backgroundColor: activeTab === 'editor' ? 'var(--primary)' : 'transparent', border: activeTab === 'editor' ? 'none' : '1px solid var(--border-color)' }}
          >
            <Code size={16} /> DSL Editor
          </button>
        </div>
      </header>

      {activeTab === 'chat' ? (
        <>
          <div className="messages-area">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '40px' }}>
                <p>Welcome to the Dify vNext Runtime Demo.</p>
                <p>Try asking: "My EC2 instance is down"</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}>
                <div className="avatar">
                  {msg.role === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="#3b82f6" />}
                </div>
                <div className="bubble">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message bot">
                <div className="avatar">
                  <Bot size={20} color="#3b82f6" />
                </div>
                <div className="bubble">
                  <Loader2 className="animate-spin" size={20} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <form onSubmit={sendMessage} className="input-box">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message..."
                disabled={loading}
              />
              <button type="submit" disabled={loading || !input.trim()}>
                <Send size={18} />
                Send
              </button>
            </form>
          </div>
        </>
      ) : (
        <div className="editor-area" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px', gap: '10px' }}>
          <div className="editor-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>aws_support.yaml</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {saveStatus && <span style={{ color: saveStatus.includes('Error') ? 'red' : 'lightgreen', fontSize: '0.9rem' }}>{saveStatus}</span>}
              <button onClick={saveDSL} disabled={saving}>
                {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                Save & Reload
              </button>
            </div>
          </div>
          <textarea
            value={dslContent}
            onChange={(e) => setDslContent(e.target.value)}
            style={{
              flex: 1,
              backgroundColor: '#1e1e1e',
              color: '#d4d4d4',
              fontFamily: 'monospace',
              fontSize: '14px',
              padding: '15px',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              resize: 'none',
              outline: 'none',
              lineHeight: '1.5'
            }}
            spellCheck="false"
          />
        </div>
      )}
    </div>
  )
}

export default App
