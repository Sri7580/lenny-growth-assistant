interface Props {
  provider: string;
  onChange: (p: string) => void;
}

export default function ModelSelector({ provider, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-400">Model:</span>
      <select
        value={provider}
        onChange={(e) => onChange(e.target.value)}
        className="border border-slate-200 rounded-md px-2 py-1 bg-white text-slate-700"
      >
        <option value="ollama">Local (Ollama)</option>
        <option value="anthropic">Cloud (Claude)</option>
      </select>
    </div>
  );
}
