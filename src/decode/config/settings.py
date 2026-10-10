from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    max_output_lines: int = 2000
    max_output_bytes: int = 50_000

    def __post_init__(self) -> None:
        if self.max_output_lines <= 0:
            raise ValueError("max_output_lines must be positive")

        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        
settings=Settings()