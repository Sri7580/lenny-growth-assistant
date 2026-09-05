interface Props {
  html: string;
}

/**
 * Security note: sandbox="allow-scripts" WITHOUT "allow-same-origin" is deliberate.
 * This lets generated HTML run JS for interactivity, but the iframe is treated as
 * an opaque/null origin — it cannot access this page's cookies, localStorage,
 * parent DOM, or make same-origin credentialed requests back to our API.
 * Content is also run through DOMPurify before reaching srcDoc as defense in depth.
 */
export default function SandboxedIframe({ html }: Props) {
  return (
    <iframe
      title="artifact-preview"
      srcDoc={html}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
    />
  );
}
