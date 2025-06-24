"use client"

import { useState } from 'react'
import type { KeyboardEvent, ChangeEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Message {
  role: 'user' | 'bot'
  content: string
}

const Chatbot = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', content: '안녕하세요! 무엇을 도와드릴까요?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage: Message = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage] })
      })
      const data = await res.json()
      const botMessage: Message = { role: 'bot', content: data.response ?? '...' }
      setMessages((prev) => [...prev, botMessage])
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'bot', content: '에러가 발생했습니다.' }])
    }
    setLoading(false)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage()
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  return (
    <Card className="w-full max-w-md">
      <CardContent className="p-4">
        <ScrollArea className="h-80 mb-3 space-y-2">
          {messages.map((msg, i) => (
            <div key={i} className={`w-full flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <span
                className={`inline-block rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === 'user' ? 'bg-teal-100' : 'bg-lime-100'
                }`}
              >
                {msg.content}
              </span>
            </div>
          ))}
          {loading && <div className="text-sm text-gray-500">답변 작성중...</div>}
        </ScrollArea>
        <div className="flex gap-2">
          <Input
            className="flex-1"
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요"
          />
          <Button onClick={sendMessage}>전송</Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default Chatbot 