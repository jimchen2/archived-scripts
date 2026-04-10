// ChatPage.tsx
"use client";

import React, { useState, useRef, useEffect } from "react";
import { modelConfigs } from "./modelConfigs";
import ConfigPanel from "./ConfigPanel";
import Chat from "./Chat";
import { handleSubmit } from "./chatUtils";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState<string>("");
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);

  // Configuration state
  const [selectedModel, setSelectedModel] = useState<string>(Object.keys(modelConfigs)[0]);
  const [system, setSystem] = useState<string>("");
  const [maxTokens, setMaxTokens] = useState<number>(1000);
  const [temperature, setTemperature] = useState<number>(0.7);
  const [topP, setTopP] = useState<number>(0.9);
  const [topK, setTopK] = useState<number>(50);
  const [presencePenalty, setPresencePenalty] = useState<number>(0);
  const [frequencyPenalty, setFrequencyPenalty] = useState<number>(0);
  const [maxInputCharacters, setMaxInputCharacters] = useState<number>(4000);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentAssistantMessage]);

  const onSubmit = (e: React.FormEvent) => {
    handleSubmit(e, {
      input,
      messages,
      selectedModel,
      system,
      maxTokens,
      temperature,
      topP,
      topK,
      presencePenalty,
      frequencyPenalty,
      maxInputCharacters,
      setMessages,
      setInput,
      setCurrentAssistantMessage,
      setIsLoading,
      setError,
    });
  };

  const configPanelContent = (
    <ConfigPanel
      selectedModel={selectedModel}
      setSelectedModel={setSelectedModel}
      system={system}
      setSystem={setSystem}
      maxTokens={maxTokens}
      setMaxTokens={setMaxTokens}
      temperature={temperature}
      setTemperature={setTemperature}
      topP={topP}
      setTopP={setTopP}
      topK={topK}
      setTopK={setTopK}
      presencePenalty={presencePenalty}
      setPresencePenalty={setPresencePenalty}
      frequencyPenalty={frequencyPenalty}
      setFrequencyPenalty={setFrequencyPenalty}
      maxInputCharacters={maxInputCharacters}
      setMaxInputCharacters={setMaxInputCharacters}
    />
  );

  return (
    <div className="flex flex-col md:flex-row h-screen">
      {/* Desktop layout */}
      <div className="hidden md:block md:w-80 flex-shrink-0 border-r border-gray-200 overflow-y-auto">{configPanelContent}</div>
      {/* Mobile layout */}
      <div className="md:hidden">
        <button onClick={() => setIsConfigOpen(!isConfigOpen)} className="w-full bg-gray-200 p-2 text-center">
          {isConfigOpen ? "Hide Config" : "Show Config"}
        </button>
        {isConfigOpen && <div className="bg-white border-t border-gray-200 p-4 overflow-auto max-h-64">{configPanelContent}</div>}
      </div>

      {/* Shared chat component */}
      <div className="flex-grow flex flex-col overflow-hidden">
        <Chat
          messages={messages}
          currentAssistantMessage={currentAssistantMessage}
          isLoading={isLoading}
          error={error}
          input={input}
          setInput={setInput}
          handleSubmit={onSubmit}
          messagesEndRef={messagesEndRef}
        />
      </div>
    </div>
  );
};

export default ChatPage;