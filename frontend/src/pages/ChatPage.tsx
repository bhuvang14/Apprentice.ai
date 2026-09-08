import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { chatApi } from '../services/api';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import type { Message, ChatRequest } from '../types';
import { v4 as uuidv4 } from 'uuid';

export function ChatPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{ role: string; content: string }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSend = async (message: string) => {
    if (!user) return;
    
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
  console.log("FRONTEND USER ID:", user.id);

  const request: ChatRequest = {
    message,
    user_id: user.id,
    conversation_history: conversationHistory,
  };
      
      const response = await chatApi.sendMessage(request);
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        generated_file: response.generated_file,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: response.response },
      ]);
    } catch (error) {
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  if (authLoading) {
    return <div className="loading">Loading...</div>;
  }
  
  if (!user) {
    return <div className="no-user">Please log in to use the chat</div>;
  }
  
  return (
    <div className="chat-page">
      <header className="chat-header">
        <h1>Faculty Template Assistant</h1>
        <div className="user-info">
          <span>{user.name} ({user.department || 'No Department'})</span>
        </div>
      </header>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Hello! I'm your Faculty Template Assistant. I can help you fill out administrative documents like:</p>
            <ul>
              <li>Syllabus templates</li>
              <li>Travel reimbursement forms</li>
              <li>Leave request forms</li>
              <li>And more...</li>
            </ul>
            <p>Just tell me what you need to work on!</p>
          </div>
        )}
        {messages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}