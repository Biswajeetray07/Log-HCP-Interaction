import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addUserMessage, addAIMessage, setLoading } from '../../features/chat/chatSlice';
import { sendChatMessage } from '../../services/api';

const ChatInput = () => {
  const [input, setInput] = useState('');
  const dispatch = useDispatch();
  const loading = useSelector((state) => state.chat.loading);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    dispatch(addUserMessage(userText));
    dispatch(setLoading(true));

    try {
      const result = await sendChatMessage(userText);
      dispatch(addAIMessage(result.response));
    } catch (error) {
      dispatch(addAIMessage("Sorry, there was an issue connecting to the AI system."));
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="bg-slate-900 border-t border-slate-800 p-4 shrink-0">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Log an interaction, fetch data, or ask for insights..."
          disabled={loading}
          className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white font-medium px-6 py-3 rounded-xl transition duration-200"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
