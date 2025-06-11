import React, { useState } from 'react';
import { MessageInput } from './MessageInput';
import { MessageList, type Message } from './MessageList';
import { sendChatMessage } from '../apiClient';

export const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (text: string) => {
    setIsLoading(true);
    const userMessage: Message = { id: Date.now(), text, sender: 'user' };
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    try {
      const aiResponse = await sendChatMessage(text, 1); // Using a placeholder user_id=1
      const aiMessage: Message = { id: Date.now() + 1, text: aiResponse.response, sender: 'ai' };
      setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: 'Sorry, something went wrong. Please try again.',
        sender: 'ai',
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-100 dark:bg-gray-800">
      <header className="bg-white dark:bg-gray-900 p-4 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <h1 className="text-xl font-semibold text-gray-800 dark:text-white text-center">Greenstein AI</h1>
      </header>
      <div className="flex-1 p-4 overflow-y-auto">
        <MessageList messages={messages} />
      </div>
      <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <MessageInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};
