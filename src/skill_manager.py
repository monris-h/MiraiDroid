"""
Skill Manager - crear y listar skills
"""
from pathlib import Path
from src.config import BASE_DIR
from src.memory import memory


class SkillManager:
    def __init__(self):
        self.skills_dir = BASE_DIR / "skills"

    def create_skill(self, name, code):
        (self.skills_dir / f"{name}.py").write_text(code)
        memory.data.setdefault("skills", []).append(name)
        memory.save()
        return True

    def list_skills(self):
        return [f.stem for f in self.skills_dir.glob("*.py")]

skill_manager = SkillManager()