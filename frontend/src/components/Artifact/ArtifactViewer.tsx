import { useMemo } from "react";
import DOMPurify from "dompurify";
import SandboxedIframe from "./SandboxedIframe";

export interface Artifact {
  artifact_type: "markdown" | "html";
  title: string;
  content: string;
}

interface Props {
  artifact: Artifact | null;
  onClose: () => void;
}

// Extremely small markdown-ish renderer, avoids pulling react-markdown for the demo.
// Handles headers, bold, bullet lists, and paragraphs — enough for Ship30/30 output.
function renderMarkdown(md: string): string {
  const escaped = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const lines = escaped.split("\n");
  const html: string[] = [];
  let inList = false;

  for (const line of lines) {
    if (/^###\s+/.test(line)) {
      html.push(`<h3>${line.replace(/^###\s+/, "")}</h3>`);
    } else if (/^##\s+/.test(line)) {
      html.push(`<h2>${line.replace(/^##\s+/, "")}</h2>`);
    } else if (/^#\s+/.test(line)) {
      html.push(`<h1>${line.replace(/^#\s+/, "")}</h1>`);
    } else if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${line.replace(/^[-*]\s+/, "")}</li>`);
    } else {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      if (line.trim()) html.push(`<p>${line}</p>`);
    }
  }
  if (inList) html.push("</ul>");

  let result = html.join("\n");
  result = result.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  return result;
}

export default function ArtifactViewer({ artifact, onClose }: Props) {
  const safeHtml = useMemo(() => {
    if (!artifact) return "";
    const raw =
      artifact.artifact_type === "markdown"
        ? renderMarkdown(artifact.content)
        : artifact.content;
    return DOMPurify.sanitize(raw, { ADD_ATTR: ["target"] });
  }, [artifact]);

  if (!artifact) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm p-8 text-center">
        Artifacts you generate (essays, HTML snippets) will appear here.
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <span className="text-xs uppercase tracking-wide text-slate-400">
            {artifact.artifact_type}
          </span>
          <h2 className="text-sm font-semibold text-slate-800">{artifact.title}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-700 text-sm px-2"
        >
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-auto">
        {artifact.artifact_type === "html" ? (
          <SandboxedIframe html={safeHtml} />
        ) : (
          <div
            className="prose prose-sm max-w-none p-4"
            dangerouslySetInnerHTML={{ __html: safeHtml }}
          />
        )}
      </div>
    </div>
  );
}
