import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentInteraction: null,
  history: [],
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    // Add reducers here later when structuring DB fetching
  },
});

export default interactionSlice.reducer;
