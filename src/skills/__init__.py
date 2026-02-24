"""
SENTINEL SKILLS MODULE

Dynamic skill injection for context-aware agent prompts.

Skills are loaded lazily based on context to save tokens.
Only relevant skills are injected into agent prompts.
"""

from .skill_registry import (
    # Core classes
    SkillRegistry,
    SkillMetadata,
    SkillTrigger,
    # Convenience functions
    get_skill_registry,
    inject_skills_into_prompt,
)

__all__ = [
    # Core classes
    "SkillRegistry",
    "SkillMetadata",
    "SkillTrigger",
    # Convenience functions
    "get_skill_registry",
    "inject_skills_into_prompt",
]
