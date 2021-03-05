import time
import asyncio

_SOCKET_NAME = "chatsock"

async def check_error( reader ):
    got = await reader.readline()
    assert got.decode().startswith("(error "), f"{got} == (error... )"

async def check_line( reader, expect ):
    expect += '\n'
    got = await reader.readline()
    assert got.decode() == f"{expect}", f"{got} == {expect}"

async def check_ok( reader ):
    expect = '(ok)\n'
    got = await reader.readline()
    assert got.decode() == f"{expect}", f"{got} == {expect}"


class Test:

    async def basic():
        pass

def main():
    async def main_simple():
        await Test.basic()

    asyncio.run( main_simple() )

if __name__ == "__main__":
    main()

