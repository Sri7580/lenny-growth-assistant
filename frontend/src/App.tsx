import { useState, useEffect, useCallback } from "react";
import { createSession, getSessionMessages } from "./lib/api";
import { useChatStream } from "./hooks/useChatStream";
import ChatPane from "./components/Chat/ChatPane";
import ArtifactViewer, { type Artifact } from "./components/Artifact/ArtifactViewer";

const STORAGE_KEY = "lenny-session-id";

function extractArtifact(text: string): Artifact | null {
  const match = text.match(
    /<artifact type="(markdown|html)" title="([^"]*)">([\s\S]*?)<\/artifact>/
  );
  if (!match) return null;
  return {
    artifact_type: match[1] as "markdown" | "html",
    title: match[2] || "Untitled",
    content: match[3].trim(),
  };
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const { messages, setMessages, sendMessage, isStreaming, error } = useChatStream(sessionId);

  useEffect(() => {
    async function init() {
      const existingId = localStorage.getItem(STORAGE_KEY);
      if (existingId) {
        try {
          const history = await getSessionMessages(existingId);
          setSessionId(existingId);
          setMessages(history);
          return;
        } catch {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
      const s = await createSession("New chat");
      localStorage.setItem(STORAGE_KEY, s.id);
      setSessionId(s.id);
    }
    init();
  }, []);

  useEffect(() => {
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (lastAssistant) {
      const found = extractArtifact(lastAssistant.content);
      if (found) setArtifact(found);
    }
  }, [messages]);

  const handleSend = useCallback(
    (text: string, prov: string) => {
      sendMessage(text, prov);
    },
    [sendMessage]
  );

  const handleNewChat = useCallback(async () => {
    const s = await createSession("New chat");
    localStorage.setItem(STORAGE_KEY, s.id);
    setSessionId(s.id);
    setMessages([]);
    setArtifact(null);
  }, [setMessages]);

  return (
    <div className="h-screen w-screen flex bg-white">
      <div className="w-1/2 border-r border-slate-200 flex flex-col">
        <div className="flex justify-end px-4 pt-2">
          <button
            onClick={handleNewChat}
            className="text-xs text-slate-400 hover:text-slate-700"
          >
            + New chat
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <ChatPane
            messages={messages}
            isStreaming={isStreaming}
            provider={provider}
            onProviderChange={setProvider}
            onSend={handleSend}
            error={error}
          />
        </div>
      </div>
      <div className="w-1/2">
        <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
      </div>
    </div>
  );
}
