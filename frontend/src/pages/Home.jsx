import React, { useState } from 'react';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import InteractionForm from '../components/form/InteractionForm';

const Home = () => {
  const [activeMode, setActiveMode] = useState('chat'); // 'chat' or 'form'

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col bg-slate-950">
      
      {/* Mode Toggle Header */}
      <div className="w-full flex justify-center py-4 border-b border-slate-900">
        <div className="bg-slate-800 p-1 rounded-lg inline-flex shadow-sm">
          <button 
            onClick={() => setActiveMode('chat')}
            className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
              activeMode === 'chat' 
                ? 'bg-blue-600 text-white shadow' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Chat Mode
          </button>
          <button 
            onClick={() => setActiveMode('form')}
            className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
              activeMode === 'form' 
                ? 'bg-blue-600 text-white shadow' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Form Mode
          </button>
        </div>
      </div>

      {/* Main Core View Area */}
      <div className="flex-1 w-full max-w-4xl mx-auto flex flex-col shadow-2xl relative bg-slate-900 border-x border-slate-800 overflow-hidden">
        
        {activeMode === 'chat' ? (
          <>
            <ChatWindow />
            <ChatInput />
          </>
        ) : (
          <InteractionForm />
        )}
        
      </div>
    </div>
  );
};

export default Home;
