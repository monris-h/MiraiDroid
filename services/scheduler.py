"""
Scheduler - cron jobs para tareas periódicas
"""
import time
import asyncio

class CronScheduler:
    def __init__(self):
        self.jobs = {}
        self.running = False

    def add_job(self, job_id, interval_seconds, task_fn):
        self.jobs[job_id] = {"interval": interval_seconds, "last": time.time(), "task": task_fn, "enabled": True}

    async def run(self, app):
        import logging
        logger = logging.getLogger(__name__)

        self.running = True
        while self.running:
            now = time.time()
            for job_id, job in list(self.jobs.items()):
                if job["enabled"] and now - job["last"] >= job["interval"]:
                    try:
                        await job["task"](app)
                        job["last"] = now
                    except Exception as e:
                        logger.error(f"Cron job error {job_id}: {e}")
            await asyncio.sleep(10)

    def enable(self, job_id, enabled=True):
        if job_id in self.jobs:
            self.jobs[job_id]["enabled"] = enabled

    def list_jobs(self):
        return [f"{jid} ({j['interval']}s, {'ON' if j['enabled'] else 'OFF'})" for jid, j in self.jobs.items()]

cron_scheduler = CronScheduler()