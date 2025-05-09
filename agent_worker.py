import time
import schedule
from app import load_agents, agent_task

def run_scheduler():
    while True:
        agents = load_agents()
        schedule.clear()
        for agent in agents:
            if agent.get('enabled'):
                if agent.get('frequency_minutes', 0) > 0:
                    schedule.every(int(agent['frequency_minutes'])).minutes.do(agent_task, agent)
                elif agent.get('frequency_hours', 0) > 0:
                    schedule.every(int(agent['frequency_hours'])).hours.do(agent_task, agent)
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("[Agent Worker] Starting agent scheduler...")
    run_scheduler() 