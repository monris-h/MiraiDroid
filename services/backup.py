"""
Backup Manager - crea y restaura backups del código
"""
import time
from pathlib import Path

class BackupManager:
    def __init__(self):
        from src.config import BASE_DIR
        self.backup_dir = BASE_DIR / "backups"
        self.max_backups = 10

    def create_backup(self, reason="manual"):
        from src.config import BASE_DIR
        import logging

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"v{timestamp}_{reason}.py"
        agent_file = BASE_DIR / "miraidroid.py"

        if agent_file.exists():
            with open(agent_file, "r") as src:
                with open(backup_file, "w") as dst:
                    dst.write(f"# Backup {timestamp} - {reason}\n")
                    dst.write(src.read())

        backups = sorted(self.backup_dir.glob("v*.py"))
        for old in backups[:-self.max_backups]:
            old.unlink()

        logging.getLogger(__name__).info(f"Backup created: {timestamp}")
        return timestamp

    def restore_backup(self, timestamp):
        from src.config import BASE_DIR
        backup_file = self.backup_dir / f"v{timestamp}_manual.py"
        if backup_file.exists():
            content = backup_file.read_text()
            content = content.replace(f"# Backup {timestamp} - manual\n", "")
            (BASE_DIR / "miraidroid.py").write_text(content)
            return True
        return False

    def list_backups(self):
        return sorted([f.stem[1:] for f in self.backup_dir.glob("v*.py")], reverse=True)

backup_manager = BackupManager()