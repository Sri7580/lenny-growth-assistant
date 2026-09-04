from typing import AsyncGenerator
from anthropic import AsyncAnthropic

from app.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None
        self.model = model

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            yield "[Error: ANTHROPIC_API_KEY not set. Add it to .env to use the cloud provider.]"
            return
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Error: Anthropic request failed — {e}]"
