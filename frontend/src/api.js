import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1', // Proxy will handle this in Vite
});

export const fetchResources = async (filters = {}) => {
    // Filter out undefined or null values
    const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v != null && v !== '')
    );
    const params = new URLSearchParams(cleanFilters);
    const response = await api.get(`/resources?${params}`);
    return response.data;
};

export const fetchResourceStats = async () => {
    const response = await api.get('/resources/stats');
    return response.data;
};

export const sendChatMessage = async (message, history = []) => {
    const response = await api.post('/chat', { message, history });
    return response.data;
};

export const submitFeedback = async (resourceId, voteType, reason) => {
    const response = await api.post(`/resources/${resourceId}/feedback`, {
        vote_type: voteType,
        reason: reason
    });
    return response.data;
};

export default api;
