import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { sendChatMessage } from '../services/api'

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hi! I'm FileFerry AI Agent. I can help you with S3 file transfers, bucket exploration, and transfer management. What would you like to do?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  const mutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        },
      ])
    },
  })

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    mutation.mutate({ message: input, user_id: 'slack_user_123' })
    setInput('')
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card p-0 overflow-hidden">
        {/* Chat Header */}
        <div className="bg-slack-purple text-white p-4 flex items-center space-x-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <Bot size={20} />
          </div>
          <div>
            <h3 className="font-semibold">FileFerry AI Agent</h3>
            <p className="text-xs opacity-90">Powered by AWS Bedrock Claude 3.5 Sonnet</p>
          </div>
        </div>

        {/* Messages */}
        <div className="h-[500px] overflow-y-auto p-6 space-y-4 bg-gray-50">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          {mutation.isPending && (
            <div className="flex items-center space-x-2 text-gray-500">
              <Loader2 className="animate-spin" size={16} />
              <span className="text-sm">AI is thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about S3 transfers..."
              className="input flex-1"
              disabled={mutation.isPending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || mutation.isPending}
              className="btn-primary px-6"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Try: "List my S3 buckets" or "Transfer file.txt from bucket-a to FTP server"
          </p>
        </div>
      </div>
    </div>
  )
}

function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex space-x-3 max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-slack-blue' : 'bg-slack-purple'
        }`}>
          {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
        </div>
        <div>
          <div className={`rounded-lg p-4 ${
            isUser ? 'bg-slack-blue text-white' : 'bg-white text-gray-900 border border-gray-200'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  )
}
