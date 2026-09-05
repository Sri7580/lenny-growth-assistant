import { useState, useRef, useEffect } from "react";
import type { Message } from "../../lib/api";
import MessageItem from "./MessageItem";
import ModelSelector from "./ModelSelector";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  provider: string;
  onProviderChange: (p: string) => void;
  onSend: (text: string, provider: string) => void;
  error: string | null;
}

export default function ChatPane({
  messages,
  isStreaming,
  provider,
  onProviderChange,
  onSend,
  error,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSend(input, provider);
    setInput("");
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h1 className="text-sm font-semibold text-slate-800">Lenny Growth Assistant</h1>
        <ModelSelector provider={provider} onChange={onProviderChange} />
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-slate-400 text-sm text-center mt-12">
            Ask a product or growth question grounded in Lenny's Podcast transcripts.
          </div>
        )}
        {messages.map((m) => (
          <MessageItem key={m.id} message={m} />
        ))}
        {error && (
          <div className="text-red-500 text-xs bg-red-50 rounded-md px-3 py-2">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-200 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about product-market fit, growth loops, pricing…"
          disabled={isStreaming}
          className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          className="bg-slate-900 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-40"
        >
          {isStreaming ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
