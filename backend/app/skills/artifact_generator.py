"""
Detects and extracts artifact blocks the LLM emits in its response.

Expected format in model output:
    <artifact type="markdown" title="My Essay">
    ...content...
    </artifact>
or
    <artifact type="html" title="Landing Page">
    ...content...
    </artifact>
"""
import re

ARTIFACT_PATTERN = re.compile(
    r'<artifact type="(?P<type>markdown|html)" title="(?P<title>[^"]*)">\s*(?P<content>.*?)\s*</artifact>',
    re.DOTALL,
)

ARTIFACT_INSTRUCTION = """If the user asks you to create a document, essay, or HTML snippet as a
standalone artifact, wrap it exactly like this:
<artifact type="markdown" title="Short Title Here">
...content...
</artifact>
or for HTML:
<artifact type="html" title="Short Title Here">
...content...
</artifact>
Only use this wrapper when the user wants a distinct, savable artifact — not for normal
conversational answers."""


def extract_artifacts(response_text: str) -> tuple[str, list[dict]]:
    """Strips artifact blocks out of the response text and returns them separately."""
    artifacts = []
    for match in ARTIFACT_PATTERN.finditer(response_text):
        artifacts.append({
            "artifact_type": match.group("type"),
            "title": match.group("title") or "Untitled",
            "content": match.group("content").strip(),
        })
    cleaned_text = ARTIFACT_PATTERN.sub("", response_text).strip()
    return cleaned_text, artifacts
