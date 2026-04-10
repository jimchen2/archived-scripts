// src/components/chatUtils.ts
import { modelConfigs } from "./modelConfigs";
import { getApiKey } from "./auth";

interface Message {
  role: "user" | "assistant";
  content: string;
}


const truncateMessages = (messages: Message[], maxChars: number): Message[] => {
  let totalChars = 0;
  let result: Message[] = [];

  // Iterate over the messages from the end to ensure we truncate from the end.
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    const messageLength = msg.content.length;

    // If adding this message exceeds maxChars, stop the process.
    if (totalChars + messageLength > maxChars) {
      break;
    }

    // Add the message and update the total character count.
    totalChars += messageLength;
    result.unshift(msg);
  }

  // Ensure that the first message in the result is from the user.
  while (result.length > 0 && result[0].role !== "user") {
    result.shift();  // Remove the first message until we find one from the user.
  }

  return result;
};

const sanitizeMessages = (messages: Message[]): Message[] => {
  let sanitizedMessages: Message[] = [];
  let currentRole: string | null = null;
  let currentContent: string = '';

  for (const msg of messages) {
    if (msg.role !== currentRole) {
      if (currentRole) {
        sanitizedMessages.push({ role: currentRole, content: currentContent.trim() });
      }
      currentRole = msg.role;
      currentContent = msg.content;
    } else {
      currentContent += '\n' + msg.content;
    }
  }

  if (currentRole) {
    sanitizedMessages.push({ role: currentRole, content: currentContent.trim() });
  }

  return sanitizedMessages;
};

export const handleSubmit = async (
  e: React.FormEvent,
  {
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
  }: {
    input: string;
    messages: Message[];
    selectedModel: string;
    system: string;
    maxTokens: number;
    temperature: number;
    topP: number;
    topK: number;
    presencePenalty: number;
    frequencyPenalty: number;
    maxInputCharacters: number;
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    setInput: React.Dispatch<React.SetStateAction<string>>;
    setCurrentAssistantMessage: React.Dispatch<React.SetStateAction<string>>;
    setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
    setError: React.Dispatch<React.SetStateAction<string | null>>;
  }
) => {
  e.preventDefault();
  if (!input.trim()) return;

  setIsLoading(true);
  setError(null);

  let updatedMessages = [...messages, { role: "user", content: input }];
  setMessages(updatedMessages);
  setInput("");
  setCurrentAssistantMessage("");

  const apiKey = getApiKey();
  if (!apiKey) {
    setError("API key not found. Please set the API key in the configuration panel.");
    setIsLoading(false);
    return;
  }

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        messages: sanitizeMessages(truncateMessages(updatedMessages, maxInputCharacters)),
        model: modelConfigs[selectedModel].provider,
        modelName: selectedModel,
        system,
        maxTokens,
        temperature,
        topP,
        topK,
        presencePenalty,
        frequencyPenalty,
      }),
    });

    if (!response.ok) {
      throw new Error(response.status === 401 ? "Unauthorized. Please check your API key." : await response.text());
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("Response body is not readable");

    let assistantMessage = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      assistantMessage += new TextDecoder().decode(value);
      setCurrentAssistantMessage(assistantMessage);
    }

    setMessages((prev) => [...prev, { role: "assistant", content: assistantMessage }]);
    setCurrentAssistantMessage("");
  } catch (err) {
    console.error("Error in handleSubmit:", err);
    setError(err instanceof Error ? err.message : String(err));
  } finally {
    setIsLoading(false);
  }
};