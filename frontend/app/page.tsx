'use client';

import { useState, useEffect, useRef } from 'react';

type Message = {
  id: number;
  role: 'user' | 'assistant';
  content: string;
};

export default function Chat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionToken, setSessionToken] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Initialize session token on mount
  useEffect(() => {
    let token = localStorage.getItem('session_token');
    if (!token) {
      token = crypto.randomUUID();
      localStorage.setItem('session_token', token);
    }
    setSessionToken(token);
  }, []);

  // 2. Auto-scroll to bottom when messages or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

 const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now(), role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_token: sessionToken,
          messages: newMessages 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.reply || `Server returned HTTP ${response.status}`);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.reply || 'No response received.',
        },
      ]);
    } catch (error: any) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          // Display the REAL error message in the chat bubble
          content: error.message || 'An unknown error occurred.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 flex flex-col items-center">
      {/* Header */}
      <header className="w-full bg-slate-900 border-b border-slate-800 py-4 px-6 text-center shadow-sm sticky top-0 z-10">
        <h1 className="text-lg font-semibold text-white tracking-wide">
          Sydney Transit AI Planner
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Powered by TfNSW APIs & Local LLM
        </p>
      </header>

      {/* Chat Container */}
      <div className="flex-1 w-full max-w-2xl flex flex-col p-4 sm:p-6 pb-32">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-16 text-slate-500 text-sm">
              Ask about train, bus, or light rail connections across Sydney.
              <div className="mt-2 text-xs text-slate-400">
                Example: &ldquo;Find me a train from Parramatta to Central at 09:00&rdquo;
              </div>
            </div>
          )}

          {messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <span className="text-xs font-semibold text-slate-500 mb-1 px-1">
                  {isUser ? 'You' : 'Transit Assistant'}
                </span>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-white text-slate-900 border border-slate-200 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center space-x-2 text-slate-600 text-sm bg-white border border-slate-200 rounded-2xl rounded-bl-none px-4 py-3 max-w-[85%] shadow-sm">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
              <span>Querying transit service data...</span>
            </div>
          )}
          
          {/* Invisible element to act as the scroll target */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-100/90 backdrop-blur-sm border-t border-slate-200 py-4 px-4 flex justify-center">
        <form onSubmit={handleSubmit} className="w-full max-w-2xl flex gap-2">
          <input
            className="flex-1 bg-white border border-slate-300 text-slate-900 placeholder-slate-400 text-sm rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
            value={input}
            placeholder="Type your journey query..."
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium text-sm px-5 py-3 rounded-xl shadow-sm transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}