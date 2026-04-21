import React from 'react';

const ChatMessage = ({ message, sender }) => {
  const isUser = sender === 'user';

  const renderContent = () => {
    // AI responses can be JSON objects (structured) or plain strings (errors/fallbacks)
    if (typeof message.text === 'object') {
      return (
        <pre className="text-xs font-mono overflow-auto whitespace-pre-wrap">
          {JSON.stringify(message.text, null, 2)}
        </pre>
      );
    }
    return <p>{message.text}</p>;
  };

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-none'
        }`}
      >
        <div className="text-sm font-medium mb-1 opacity-70">
          {isUser ? 'You' : 'Agent'}
        </div>
        <div className="text-md leading-relaxed">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
