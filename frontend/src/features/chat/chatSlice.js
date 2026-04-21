import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  messages: [],
  loading: false,
  // Populated when the AI returns structured interaction data (with hcp_name).
  // Used by InteractionForm to auto-fill fields when switching to Form Mode.
  selectedInteraction: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({
        id: Date.now().toString(),
        text: action.payload,
        sender: 'user',
      });
    },

    addAIMessage: (state, action) => {
      const response = action.payload;

      state.messages.push({
        id: Date.now().toString(),
        text: response,
        sender: 'ai',
      });

      // When the AI returns a structured interaction (log or fetch), store it
      // so the Form tab can pre-populate. Skip non-structured responses like suggestions.
      if (response?.status === 'success' && response?.data?.hcp_name) {
        state.selectedInteraction = response.data;
      }
    },

    setLoading: (state, action) => {
      state.loading = action.payload;
    },
  },
});

export const { addUserMessage, addAIMessage, setLoading } = chatSlice.actions;
export default chatSlice.reducer;
