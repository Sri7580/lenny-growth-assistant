import { useState, useEffect, useCallback } from "react";
import { createSession } from "./lib/api";
import { useChatStream } from "./hooks/useChatStream";
import ChatPane from "./components/Chat/ChatPane";
import ArtifactViewer, { type Artifact } from "./components/Artifact/ArtifactViewer";

// Detects <artifact type="..." title="...">...</artifact> blocks client-side,
// mirroring backend/app/skills/artifact_generator.py, so the viewer can update
// live while a response is still streaming in.
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
  const { messages, sendMessage, isStreaming, error } = useChatStream(sessionId);

  useEffect(() => {
    createSession("New chat").then((s) => setSessionId(s.id));
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

  return (
    <div className="h-screen w-screen flex bg-white">
      <div className="w-1/2 border-r border-slate-200">
        <ChatPane
          messages={messages}
          isStreaming={isStreaming}
          provider={provider}
          onProviderChange={setProvider}
          onSend={handleSend}
          error={error}
        />
      </div>
      <div className="w-1/2">
        <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
      </div>
    </div>
  );
}
