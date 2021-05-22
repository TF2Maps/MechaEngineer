import random
import string
import asyncio


def get_random_password(length=8):
    characters = string.ascii_letters + string.digits
    password = "".join(random.choice(characters) for x in range(length))

    return password


async def wait_for_tcp(ip, port, retries=60):
    for i in range(retries):
        try:
            _, writer = await asyncio.open_connection(ip, port)
            writer.close()
            await writer.wait_closed()
            return True
        except ConnectionRefusedError as e:
            await asyncio.sleep(5)
    else:
        return False
