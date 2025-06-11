import React from 'react';

export interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
}

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
              msg.sender === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
            }`}>
            {msg.text}
          </div>
        </div>
      ))}
    </div>
  );
};
