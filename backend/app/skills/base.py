from abc import ABC, abstractmethod


class ClaudeSkill(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema properties object

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        raise NotImplementedError

    def get_tool_schema(self) -> dict:
        """Return the tool schema Claude expects in the `tools` list."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self._required_params(),
            },
        }

    def _required_params(self) -> list[str]:
        return [
            k for k, v in self.parameters.items()
            if not v.get("optional", False)
        ]
