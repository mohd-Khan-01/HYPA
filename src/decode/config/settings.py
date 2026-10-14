from dataclasses import dataclass,field
import os
from dotenv import load_dotenv

load_dotenv()
@dataclass(frozen=True, slots=True)
class Settings:
    max_output_lines: int = 100
    max_output_bytes: int = 5000
    groq_model: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_MODEL", "openai/gpt-oss-20b"
        )
    )

    def __post_init__(self) -> None:
        if self.max_output_lines <= 0:
            raise ValueError("max_output_lines must be positive")

        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        
settings=Settings()