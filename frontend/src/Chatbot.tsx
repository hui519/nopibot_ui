"use client"

import React, { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent, ChangeEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Message {
  role: 'user' | 'bot'
  content: string
  timestamp: Date
  selected_mode?: string
  complexity?: string
  question_type?: string
  urgency?: string
  quality_score?: string
  auto_selection?: boolean
}

const ChatbotComponent: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'bot',
      content: '안녕하세요! \nkenopi 고객지원팀 노피🤖입니다. 무엇을 도와드릴까요?',
      timestamp: new Date(),
      selected_mode: 'auto',
      auto_selection: true
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const getModeIcon = (mode?: string) => {
    switch (mode) {
      case 'basic': return '💬'
      case 'thinking': return '🧠'
      case 'enhanced': return '⚡'
      case 'auto': return '🎯'
      default: return '🤖'
    }
  }

  const getModeLabel = (mode?: string) => {
    switch (mode) {
      case 'basic': return '기본 모드'
      case 'thinking': return '추론 모드'
      case 'enhanced': return '고급 모드'
      case 'auto': return '자동 선택'
      default: return '자동'
    }
  }

  const getComplexityColor = (complexity?: string) => {
    switch (complexity) {
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getUrgencyIcon = (urgency?: string) => {
    switch (urgency) {
      case 'high': return '🚨'
      case 'medium': return '⚠️'
      case 'low': return '📝'
      default: return ''
    }
  }

  const getQuestionTypeIcon = (type?: string) => {
    switch (type) {
      case 'complaint': return '😤'
      case 'inquiry': return '❓'
      case 'request': return '🙏'
      case 'greeting': return '👋'
      default: return '💬'
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return
    
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    
    try {
      const endpoint = showDetails ? '/api/kenopi/chat/advanced' : '/api/kenopi/chat'
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages.concat(userMessage).map(m => ({
            role: m.role,
            content: m.content
          })),
        }),
      })
      
      if (!response.ok) {
        throw new Error('응답을 받을 수 없습니다')
      }
      
      const data = await response.json()
      
      const botMessage: Message = {
        role: 'bot',
        content: data.response,
        timestamp: new Date(),
        selected_mode: data.selected_mode,
        complexity: data.complexity,
        question_type: data.question_type,
        urgency: data.urgency,
        quality_score: data.quality_score,
        auto_selection: data.auto_selection
      }
      
      setMessages(prev => [...prev, botMessage])
      
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        role: 'bot',
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
        timestamp: new Date(),
        selected_mode: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([
      {
        role: 'bot',
        content: '안녕하세요! \nkenopi 고객지원팀 노피🤖입니다. 무엇을 도와드릴까요?',
        timestamp: new Date(),
        selected_mode: 'auto',
        auto_selection: true
      }
    ])
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <Card className="flex-1 flex flex-col">
        <CardHeader className="flex-shrink-0 border-b">
          <div className="flex justify-between items-center">
            <CardTitle className="text-xl font-bold text-blue-600">
              ⛱️ AI 고객지원 Nopi🤖
            
            </CardTitle>
            <div className="flex gap-2 items-center">
              {/* <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? '간단히' : '상세히'}
              </Button> */}
              <Button
                variant="outline"
                size="sm"
                onClick={clearChat}
              >
                새 대화
              </Button>
            </div>
          </div>
          
          {/* 자동 모드 설명 */}
        
          {/* <div className="text-sm text-gray-600 mt-2 bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-blue-600 font-medium">🎯 자동 모드 선택 활성화</span>
            </div>
            <div className="text-xs">
              AI가 질문을 분석하여 자동으로 최적의 응답 방식을 선택합니다:
              <span className="mx-2">💬 간단 → 기본</span>
              <span className="mx-2">🧠 보통 → 추론</span>
              <span className="mx-2">⚡ 복잡 → 고급</span>
            </div>
          </div> */}

        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-0">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {/* 봇 응답의 자동 선택 정보 */}
                    {message.role === 'bot' && message.auto_selection && (
                      <div className="flex items-center gap-2 mb-2 text-xs">
                        <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
                          {getModeIcon(message.selected_mode)}
                          <span className="font-medium">{getModeLabel(message.selected_mode)}</span>
                          <span className="text-blue-500">자동선택</span>
                        </span>
                      </div>
                    )}

                    {/* 상세 분석 정보 (상세히 모드일 때) */}
                    {message.role === 'bot' && showDetails && message.complexity && (
                      <div className="flex flex-wrap gap-1 mb-2 text-xs">
                        {/* 복잡도 */}
                        <span className={`px-2 py-1 rounded-full ${getComplexityColor(message.complexity)}`}>
                          복잡도: {message.complexity}
                        </span>
                        
                        {/* 질문 유형 */}
                        {message.question_type && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                            {getQuestionTypeIcon(message.question_type)} {message.question_type}
                          </span>
                        )}
                        
                        {/* 긴급도 */}
                        {message.urgency && (
                          <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full">
                            {getUrgencyIcon(message.urgency)} {message.urgency}
                          </span>
                        )}
                        
                        {/* 품질 점수 */}
                        {message.quality_score && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
                            품질: {message.quality_score}
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* 메시지 내용 */}
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {/* 자동 선택 설명 (상세 모드) */}
                    {message.role === 'bot' && showDetails && message.selected_mode && message.selected_mode !== 'auto' && (
                      <div className="mt-3 p-2 bg-blue-50 rounded border-l-4 border-blue-400">
                        <div className="text-xs font-medium text-blue-700 mb-1">
                          🎯 자동 모드 선택 결과
                        </div>
                        <div className="text-xs text-blue-600">
                          {message.complexity && message.question_type && 
                            `'${message.complexity}' 복잡도의 '${message.question_type}' 유형으로 분석하여 '${getModeLabel(message.selected_mode)}'를 선택했습니다.`
                          }
                        </div>
                      </div>
                    )}
                    
                    {/* 타임스탬프 */}
                    <div className="text-xs opacity-60 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                      <span className="text-gray-600">
                        🤖 조금만 기다려주세요... 노피가 답변을 준비하고 있어요..
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div ref={messagesEndRef} />
          </ScrollArea>
          
          {/* 입력 영역 */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="🎯 질문을 입력하세요."
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="px-6"
              >
                {isLoading ? '⏳' : '전송'}
              </Button>
            </div>
            
            {/* 하단 정보 */}
            {/* <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
              <span>
                🎯 자동 모드 선택 · 🔒 개인정보 보호 · 📊 품질 보증
              </span>
              <span>
                Enter: 전송 · Shift+Enter: 줄바꿈
              </span>
            </div>
             */}
            {/* 모드 설명 */}
            {/* {!isLoading && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
                <div className="flex items-center justify-center gap-4">
                  <span className="flex items-center gap-1">💬 <strong>기본</strong>: 간단한 질문</span>
                  <span className="flex items-center gap-1">🧠 <strong>추론</strong>: 일반 문의</span>
                  <span className="flex items-center gap-1">⚡ <strong>고급</strong>: 복잡한 상황</span>
                </div>
              </div>
            )} */}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ChatbotComponent 