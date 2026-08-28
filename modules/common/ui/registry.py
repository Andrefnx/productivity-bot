from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class UIContribution:
    key: str
    label: str
    description: str
    order: int
    renderer: Callable
    public: bool = True
    requires_feature: str | None = None


class UIRegistry:
    def __init__(self, name: str):
        self.name = name
        self._entries = {}

    def register(
        self,
        key: str,
        label: str,
        description: str,
        order: int,
        renderer: Callable,
        public: bool = True,
        requires_feature: str | None = None
    ):
        if key in self._entries:
            raise ValueError(
                f"Duplicate {self.name} registry key: {key}"
            )

        self._entries[key] = UIContribution(
            key=key,
            label=label,
            description=description,
            order=order,
            renderer=renderer,
            public=public,
            requires_feature=requires_feature
        )

    def entries(self, guild_id=None):
        from modules.common.entitlements import is_feature_enabled

        return sorted(
            (
                entry
                for entry in self._entries.values()
                if entry.public
                and (
                    entry.requires_feature is None
                    or is_feature_enabled(
                        entry.requires_feature,
                        guild_id
                    )
                )
            ),
            key=lambda entry: (entry.order, entry.key)
        )

    def get(self, key: str):
        return self._entries.get(key)