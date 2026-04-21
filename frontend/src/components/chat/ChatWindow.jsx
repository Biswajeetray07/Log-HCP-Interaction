import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import ChatMessage from './ChatMessage';

const ChatWindow = () => {
  const messages = useSelector((state) => state.chat.messages);
  const loading = useSelector((state) => state.chat.loading);
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-2 relative">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center opacity-60">
          <svg className="w-16 h-16 text-slate-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <p className="text-lg font-medium text-slate-300">Welcome to AI CRM Core</p>
          <p className="text-sm text-slate-400 mt-1 max-w-sm">Log an interaction, fetch data, or ask for insights.</p>
        </div>
      ) : (
        messages.map((message) => (
          <ChatMessage key={message.id} message={message} sender={message.sender} />
        ))
      )}

      {loading && (
        <div className="flex w-full justify-start mt-2">
          <div className="bg-slate-800 border border-slate-700 text-slate-400 rounded-2xl rounded-bl-none px-5 py-3 shadow-sm inline-flex items-center space-x-2">
            <span className="animate-pulse h-2 w-2 bg-slate-500 rounded-full"></span>
            <span className="animate-pulse h-2 w-2 bg-slate-500 rounded-full animation-delay-200"></span>
            <span className="animate-pulse h-2 w-2 bg-slate-500 rounded-full animation-delay-400"></span>
            <span className="ml-2 text-sm font-medium">Agent is thinking...</span>
          </div>
        </div>
      )}
      
      <div ref={bottomRef} className="h-4" /> {/* Invisible anchor for scrolling */}
    </div>
  );
};

export default ChatWindow;
