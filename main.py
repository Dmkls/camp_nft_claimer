import asyncio
from random import randint, uniform
from core.mint import process_account
from configs import config

with open("./configs/private_keys.txt", encoding='utf-8') as file:
    PRIVATE_KEYS = [line.strip() for line in file]

print(f"Начинается минт нфт на {len(PRIVATE_KEYS)} кошельков")

async def main():
    tasks = []
    for private_key in PRIVATE_KEYS:
        task = asyncio.create_task(process_account(private_key))
        tasks.append(task)
        await asyncio.sleep(uniform(config.DELAY_BETWEEN_WALLETS[0], config.DELAY_BETWEEN_WALLETS[1]))

    while tasks:
        tasks = [task for task in tasks if not task.done()]
        await asyncio.sleep(10)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nРабота скрипта остановлена")