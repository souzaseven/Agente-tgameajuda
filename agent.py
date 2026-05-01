import anthropic
from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, MAX_HISTORY_TURNS
from prompts import SYSTEM_PROMPT
from tools import TOOL_DEFINITIONS, execute_tool


class AgentHD:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY não configurada. "
                "Crie um arquivo .env com sua chave da API Anthropic."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history: list[dict] = []
        self._system = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ]

    def get_intro(self) -> str:
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=self._system,
            messages=[
                {
                    "role": "user",
                    "content": "Inicie a sessão com sua apresentação de 2 linhas."
                }
            ]
        )
        return self._extract_text(response)

    def chat(self, user_message: str) -> dict:
        self.history.append({"role": "user", "content": user_message})
        self._trim_history()

        reply, tools_used = self._run_agent_loop()

        self.history.append({"role": "assistant", "content": reply})
        return {"text": reply, "tools_used": tools_used}

    def _run_agent_loop(self) -> tuple[str, list[str]]:
        messages = list(self.history)
        tools_used: list[str] = []

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self._system,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response), tools_used

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if block.name not in tools_used:
                            tools_used.append(block.name)
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                messages.append({"role": "user", "content": tool_results})
                continue

            return self._extract_text(response), tools_used

    def clear_history(self):
        self.history.clear()

    def get_status(self) -> dict:
        return {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "turns_in_history": len(self.history),
            "max_history_turns": MAX_HISTORY_TURNS,
            "tools_available": [t["name"] for t in TOOL_DEFINITIONS]
        }

    def _extract_text(self, response) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                parts.append(block.text)
        return "\n".join(parts).strip() or "(sem resposta em texto)"

    def _trim_history(self):
        max_messages = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
