import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { logInteraction, updateInteraction, getInteractionsForHCP, chatWithAgent } from '../../services/api';

// Async Thunks
export const logInteractionAsync = createAsyncThunk(
  'interactions/logInteraction',
  async (interactionData, { rejectWithValue }) => {
    try {
      const response = await logInteraction(interactionData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const updateInteractionAsync = createAsyncThunk(
  'interactions/updateInteraction',
  async ({ id, interactionData }, { rejectWithValue }) => {
    try {
      const response = await updateInteraction(id, interactionData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const getInteractionsForHCPAsync = createAsyncThunk(
  'interactions/getInteractionsForHCP',
  async (hcpName, { rejectWithValue }) => {
    try {
      const response = await getInteractionsForHCP(hcpName);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const chatWithAgentAsync = createAsyncThunk(
  'interactions/chatWithAgent',
  async ({ message, formData }, { rejectWithValue }) => {
    try {
      const response = await chatWithAgent(message, formData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const initialState = {
  interactions: [],
  chatResponse: null,
  status: 'idle',
  error: null,
};

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      // logInteractionAsync
      .addCase(logInteractionAsync.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(logInteractionAsync.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.interactions.push(action.payload);
      })
      .addCase(logInteractionAsync.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // updateInteractionAsync
      .addCase(updateInteractionAsync.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(updateInteractionAsync.fulfilled, (state, action) => {
        state.status = 'succeeded';
        const index = state.interactions.findIndex(int => int.id === action.payload.id);
        if (index !== -1) {
          state.interactions[index] = action.payload;
        }
      })
      .addCase(updateInteractionAsync.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // getInteractionsForHCPAsync
      .addCase(getInteractionsForHCPAsync.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(getInteractionsForHCPAsync.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.interactions = action.payload; // Assuming this replaces the list for a specific HCP
      })
      .addCase(getInteractionsForHCPAsync.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // chatWithAgentAsync
      .addCase(chatWithAgentAsync.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(chatWithAgentAsync.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.chatResponse = action.payload;
      })
      .addCase(chatWithAgentAsync.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export default interactionsSlice.reducer;