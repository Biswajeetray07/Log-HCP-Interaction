import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { sendChatMessage } from '../../services/api';

const EMPTY_FORM = {
  hcpName: '',
  specialty: '',
  product: '',
  summary: '',
  sentiment: 'Neutral',
  nextAction: '',
};

const InteractionForm = () => {
  const selectedInteraction = useSelector((state) => state.chat.selectedInteraction);

  const [formData, setFormData] = useState({ ...EMPTY_FORM });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // When the AI returns structured data (via Chat Mode), pre-fill the form
  useEffect(() => {
    if (selectedInteraction) {
      setFormData({
        hcpName: selectedInteraction.hcp_name || '',
        specialty: selectedInteraction.specialty || '',
        product: selectedInteraction.product || '',
        summary: selectedInteraction.summary || '',
        sentiment: selectedInteraction.sentiment || 'Neutral',
        nextAction: selectedInteraction.next_action || '',
      });
    }
  }, [selectedInteraction]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.hcpName || !formData.product) return;

    setLoading(true);
    setResult(null);

    // Convert form fields into a natural language string so it flows
    // through the same AI pipeline as chat messages
    const message = `Met ${formData.hcpName}, specialty ${formData.specialty || 'unknown'}, discussed ${formData.product}, sentiment ${formData.sentiment}, next action ${formData.nextAction || 'none'}. Summary: ${formData.summary || 'None'}`;

    try {
      const response = await sendChatMessage(message);
      setResult(response.response);
      setFormData({ ...EMPTY_FORM });
    } catch (error) {
      setResult({ status: 'error', message: 'Failed to connect to AI backend.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto py-6 flex flex-col h-full overflow-y-auto px-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-medium text-white">Log New Interaction</h2>
          {selectedInteraction && (
            <span className="inline-flex items-center bg-blue-900/40 text-blue-300 text-xs font-semibold px-2.5 py-1 rounded-full border border-blue-800/60 shadow-sm">
              ✨ Auto-filled by AI
            </span>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">HCP Name *</label>
              <input required type="text" name="hcpName" value={formData.hcpName} onChange={handleChange} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="e.g. Dr. Sharma" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Specialty</label>
              <input type="text" name="specialty" value={formData.specialty} onChange={handleChange} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="Not provided" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Product *</label>
            <input required type="text" name="product" value={formData.product} onChange={handleChange} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="e.g. Drug A" />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Interaction Summary</label>
            <textarea name="summary" value={formData.summary} onChange={handleChange} rows="3" className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="Brief notes on the discussion..." />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Sentiment</label>
              <select name="sentiment" value={formData.sentiment} onChange={handleChange} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Interested">Interested</option>
                <option value="Neutral">Neutral</option>
                <option value="Not Interested">Not Interested</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Next Action</label>
              <input type="text" name="nextAction" value={formData.nextAction} onChange={handleChange} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500" placeholder="e.g. Follow up in 2 weeks" />
            </div>
          </div>

          <div className="pt-2">
            <button disabled={loading} type="submit" className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-xl transition duration-200">
              {loading ? 'Processing...' : 'Submit Interaction'}
            </button>
          </div>
        </form>

        {result && (
          <div className={`mt-6 p-4 rounded-xl border ${result.status === 'success' ? 'bg-green-900/20 border-green-800/50 text-green-300' : 'bg-red-900/20 border-red-800/50 text-red-300'}`}>
            <h3 className="font-semibold mb-2">{result.status === 'success' ? 'Interaction Saved!' : 'Something went wrong'}</h3>
            {result.data ? (
              <div className="text-sm space-y-1 mt-2 opacity-90">
                <p><strong>ID:</strong> {result.data.id}</p>
                <p><strong>HCP:</strong> {result.data.hcp_name}</p>
                <p><strong>Product:</strong> {result.data.product}</p>
                <p><strong>Sentiment:</strong> {result.data.sentiment}</p>
                <p><strong>Next Steps:</strong> {result.data.next_action}</p>
              </div>
            ) : (
              <p className="text-sm opacity-90">{result.message || JSON.stringify(result)}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractionForm;
