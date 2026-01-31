"use client";

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import { ChatPanel } from '@/components/ChatPanel';
import { MapPanel } from '@/components/MapPanel';
import { Experience } from '@/types';

export default function Home() {
  const {
    messages,
    isConnected,
    isLoading,
    experiences,
    toolStatus,
    sendMessage
  } = useChat();

  const [selectedExperience, setSelectedExperience] = useState<Experience | null>(null);

  const handleExperienceClick = (experience: Experience) => {
    setSelectedExperience(experience);
  };

  return (
    <main className="h-screen w-screen flex">
      {/* Panel de Chat - 40% */}
      <div className="w-[40%] h-full border-r">
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          toolStatus={toolStatus}
          isConnected={isConnected}
          onSendMessage={sendMessage}
        />
      </div>

      {/* Panel del Mapa - 60% */}
      <div className="w-[60%] h-full" style={{ height: '100%' }}>
        <MapPanel
          experiences={experiences}
          selectedExperience={selectedExperience}
          onExperienceSelect={handleExperienceClick}
        />
      </div>
    </main>
  );
}