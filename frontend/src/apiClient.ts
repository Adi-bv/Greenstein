import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatResponse {
  response: string;
}

export const sendChatMessage = async (message: string, userId?: number): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat/', { message, user_id: userId });
    return response.data;
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
};
