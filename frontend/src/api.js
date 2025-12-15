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
    // Add trailing slash to avoid 307 redirect
    const response = await api.get(`/resources/?${params}`);
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

export const sendChatMessageStream = async (message, history = [], onChunk) => {
    // Explicitly use /api/v1 prefix which is proxied by Vite
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, history }),
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const parts = buffer.split('\n\n');
        // Keep the last part in buffer as it might be incomplete
        buffer = parts.pop();
        
        for (const part of parts) {
            if (part.startsWith('data: ')) {
                const jsonStr = part.slice(6);
                if (jsonStr === '[DONE]') return;
                try {
                    const data = JSON.parse(jsonStr);
                    onChunk(data);
                } catch (e) {
                    console.error('Error parsing SSE:', e);
                }
            }
        }
    }
};

export const submitFeedback = async (resourceId, voteType, reason) => {
    const response = await api.post(`/resources/${resourceId}/feedback`, {
        vote_type: voteType,
        reason: reason
    });
    return response.data;
};

export const generateQuestions = async (resourceId, title, summary) => {
    const response = await api.post('/chat/generate_questions', {
        resource_id: resourceId,
        resource_title: title,
        resource_summary: summary
    });
    return response.data.questions;
};

export default api;
