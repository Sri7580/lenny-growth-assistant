import type { Message } from "../../lib/api";

interface Props {
  message: Message;
}

export default function MessageItem({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
          isUser
            ? "bg-slate-900 text-white"
            : "bg-slate-100 text-slate-800"
        }`}
      >
        {message.content || (
          <span className="text-slate-400 italic">thinking…</span>
        )}
      </div>
    </div>
  );
}
