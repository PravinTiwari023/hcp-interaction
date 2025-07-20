import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
});

export const logInteraction = (interactionData) => api.post('/interactions/log', interactionData);
export const updateInteraction = (id, interactionData) => api.put(`/interactions/${id}`, interactionData);
export const getInteractionsForHCP = (hcpName) => api.get(`/interactions/hcp/${encodeURIComponent(hcpName)}`);
export const chatWithAgent = (message, formData) => api.post('/chat', { message, form_data: formData });
