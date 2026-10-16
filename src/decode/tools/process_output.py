from dataclasses import dataclass, field


@dataclass(slots=True)
class OutputCapture:
    max_bytes: int
    data: bytearray = field(
        default_factory=bytearray,
        init=False,
        repr=False,
    )
    truncated: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive.")

    def append(self, chunk: bytes) -> None:
        remaining = self.max_bytes - len(self.data)
        self.data.extend(chunk[:remaining])

        if len(chunk) > remaining:
            self.truncated = True

    def text(self) -> str:
        return self.data.decode("utf-8", errors="replace")