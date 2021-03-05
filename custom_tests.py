from shipclient import Battleship
import shipserv

import unittest
import asyncio

def get_basic_layout_1():
    return [( 0, 0, 2, False ),
            ( 0, 1, 3, False ),
            ( 0, 2, 3, False ),
            ( 0, 3, 4, False ),
            ( 0, 4, 5, False ), ]

def get_basic_layout_2():
    return [( 0, 0, 2, True ),
            ( 1, 0, 3, True ),
            ( 2, 0, 3, True ),
            ( 3, 0, 4, True ),
            ( 4, 0, 5, True ), ]


def set_layout( b: Battleship, layout ):
    for x,y,size,vertical in layout:
        b.put_ship( x, y, size, vertical )


async def shoot_layout( b: Battleship, layout ):
    for x,y,size,vertical in layout:
        for i in range(size):
            if vertical:
                await b.round(x, y+i)
            else:
                await b.round(x+i, y)


def check_states_empty( battleship ):
    assert not battleship.finished()
    assert not battleship.won()
    assert not battleship.draw()
    assert not battleship.aborted()


def check_win( b: Battleship ):
    assert b.finished()
    assert b.won()
    assert not b.draw()
    assert not b.aborted()


def check_lost( b: Battleship ):
    assert b.finished()
    assert not b.won()
    assert not b.draw()
    assert not b.aborted()

def check_draw( b: Battleship ):
    assert b.finished()
    assert not b.won()
    assert b.draw()
    assert not b.aborted()

def check_abort( b: Battleship ):
    assert b.finished()
    assert not b.won()
    assert not b.draw()
    assert b.aborted()

async def check_list( b: Battleship, *players ):
    """if absolute is set, check equality of lists."""
    ships = await b.list_games()
    for p in players:
        assert p in ships

class TestConnect_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestConnect_TwoPlayers.player_1(),
                                TestConnect_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )

        lst = await b.list_games()
        assert len(lst) == 1
        assert lst[0] == "foo"
        await b.auto()


class TestConnect_FourPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestConnect_FourPlayers.player_1(),
                                TestConnect_FourPlayers.player_2(),
                                TestConnect_FourPlayers.player_3(),
                                TestConnect_FourPlayers.player_4(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )

        lst = await b.list_games()
        assert len(lst) == 1
        assert lst[0] == "foo"
        await b.auto()

    @staticmethod
    async def player_3():
        b = Battleship()
        await b.connect(nick="baz")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )

        await asyncio.sleep(0.1)
        await b.start()

    @staticmethod
    async def player_4():
        b = Battleship()
        await b.connect(nick="baaz")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.3)

        lst = await b.list_games()
        assert len(lst) == 1
        assert lst[0] == "baz"
        await b.join( "baz" )

class TestList_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestList_TwoPlayers.player_1(),
                                TestList_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        lst = await b.list_games()
        assert len(lst) == 1
        assert lst[0] == "bar"

        set_layout( b, get_basic_layout_1() )
        await b.join( "bar" )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )

        await asyncio.sleep(0.1)
        await b.start()


class TestWin_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_TwoPlayers.player_1(),
                                TestWin_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)

        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.join( "foo" )

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_win( b )

class TestWin_StartAuto_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_StartAuto_TwoPlayers.player_1(),
                                TestWin_StartAuto_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)

        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_win( b )

class TestWin_AutoJoin_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_AutoJoin_TwoPlayers.player_1(),
                                TestWin_AutoJoin_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)

        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.join( "foo" )

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_win( b )

class TestWin_AutoAuto_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_AutoAuto_TwoPlayers.player_1(),
                                TestWin_AutoAuto_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)

        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_win( b )

class TestDraw_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestDraw_TwoPlayers.player_1(),
                                TestDraw_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.join( "foo" )

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )


class TestDraw_AutoAuto_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestDraw_AutoAuto_TwoPlayers.player_1(),
                                TestDraw_AutoAuto_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

class TestDraw_AutoJoin_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestDraw_AutoJoin_TwoPlayers.player_1(),
                                TestDraw_AutoJoin_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.join( "foo" )

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

class TestDraw_StartAuto_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestDraw_StartAuto_TwoPlayers.player_1(),
                                TestDraw_StartAuto_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )

        check_draw( b )

class TestDraw_StartAuto_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestDraw_StartAuto_Restart_TwoPlayers.player_1(),
                                TestDraw_StartAuto_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_draw( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await b.join( "bar" )

        await shoot_layout( b, get_basic_layout_2() )
        check_draw( b )


    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_draw( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        await b.start()

        await shoot_layout( b, get_basic_layout_2() )
        check_draw( b )


class TestWin_StartAuto_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_StartAuto_Restart_TwoPlayers.player_1(),
                                TestWin_StartAuto_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_win( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await b.join( "bar" )

        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        await b.start()

        await shoot_layout( b, get_basic_layout_2() )
        check_win( b )

class TestWin_AutoJoin_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_AutoJoin_Restart_TwoPlayers.player_1(),
                                TestWin_AutoJoin_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_win( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await asyncio.sleep(0.1)
        await b.join( "bar" )

        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        await b.join("foo")

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        await b.auto()

        await shoot_layout( b, get_basic_layout_2() )
        check_win( b )


class TestWin_AutoAuto_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestWin_AutoAuto_Restart_TwoPlayers.player_1(),
                                TestWin_AutoAuto_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.auto()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_win( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await asyncio.sleep(0.1)
        await b.auto()

        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        await b.auto()

        check_states_empty( b )
        for _ in range(17):
            await b.round(9, 9)
        check_lost( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        await b.auto()

        await shoot_layout( b, get_basic_layout_2() )
        check_win( b )


class TestAbort_HashMismatch_StartJoin_GoodBad_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestAbort_HashMismatch_StartJoin_GoodBad_TwoPlayers.player_1(),
                                TestAbort_HashMismatch_StartJoin_GoodBad_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        b._salt = "invalid_salt"
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_abort( b )


    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        await b.join("foo")

        check_states_empty( b )
        for i in range(17):
            await b.round(9, 9)
        check_abort( b )

class TestAbort_HashMismatch_StartJoin_BadGood_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestAbort_HashMismatch_StartJoin_BadGood_TwoPlayers.player_1(),
                                TestAbort_HashMismatch_StartJoin_BadGood_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_abort( b )


    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        b._salt = "invalid_salt"
        await b.join("foo")

        check_states_empty( b )
        for i in range(17):
            await b.round(9, 9)
        check_abort( b )

class TestAbort_HashMismatch_StartJoin_BadBad_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestAbort_HashMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_1(),
                                TestAbort_HashMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        b._salt = "invalid_salt2"
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_abort( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await asyncio.sleep(0.1)
        b._server_salt = "invalid_hash"
        await b.auto()

        for _ in range(17):
            await b.round(9, 9)
        check_abort( b )



    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        b._salt = "invalid_salt1"
        await b.join("foo")

        check_states_empty( b )
        for i in range(17):
            await b.round(9, 9)
        check_abort( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        b._server_salt = "invalid_hash"
        await b.auto()

        await shoot_layout( b, get_basic_layout_2() )
        check_abort( b )

class TestAbort_BoardMismatch_StartJoin_BadBad_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestAbort_BoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_1(),
                                TestAbort_BoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        b._ship_layout = get_basic_layout_2()
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_abort( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await asyncio.sleep(0.1)
        b._ship_layout = get_basic_layout_1()
        await b.auto()

        for _ in range(17):
            await b.round(9, 9)
        check_abort( b )



    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        b._ship_layout = get_basic_layout_2()
        await b.join("foo")

        check_states_empty( b )
        for i in range(17):
            await b.round(9, 9)
        check_abort( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        b._ship_layout = get_basic_layout_1()
        await b.auto()

        await shoot_layout( b, get_basic_layout_2() )
        check_abort( b )

class TestAbort_HashBoardMismatch_StartJoin_BadBad_Restart_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestAbort_HashBoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_1(),
                                TestAbort_HashBoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.player_2(), )

    @staticmethod
    async def player_1():
        b = Battleship()
        await b.connect(nick="foo")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        b._ship_layout = get_basic_layout_2()
        b._salt = "invalid_salt"
        await b.start()

        check_states_empty( b )
        await shoot_layout( b, get_basic_layout_1() )
        check_abort( b )

        b.restart()
        check_states_empty( b )
        await check_list( b, "bar" )
        set_layout( b, get_basic_layout_2() )
        await asyncio.sleep(0.1)
        b._ship_layout = get_basic_layout_1()
        b._salt = "invalid_salt"
        await b.auto()

        for _ in range(17):
            await b.round(9, 9)
        check_abort( b )



    @staticmethod
    async def player_2():
        b = Battleship()
        await b.connect(nick="bar")
        check_states_empty( b )

        set_layout( b, get_basic_layout_1() )
        await asyncio.sleep(0.1)
        b._ship_layout = get_basic_layout_2()
        b._salt = "invalid_salt"
        await b.join("foo")

        check_states_empty( b )
        for i in range(17):
            await b.round(9, 9)
        check_abort( b )

        b.restart()
        check_states_empty( b )
        set_layout( b, get_basic_layout_2() )
        b._ship_layout = get_basic_layout_1()
        b._salt = "invalid_salt"
        await b.auto()

        await shoot_layout( b, get_basic_layout_2() )
        check_abort( b )


class TestList_ActiveGames_Increase_TwoPlayers:


    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestList_ActiveGames_Increase_TwoPlayers.add_active_games(),
                                TestList_ActiveGames_Increase_TwoPlayers.join_active_games(),
                                TestList_ActiveGames_Increase_TwoPlayers.waiter(), )


    @staticmethod
    async def add_active_games():
        for i in range(10):
            b = Battleship()
            await b.connect(nick=f"host{i}")

            set_layout( b, get_basic_layout_1() )
            await b.start()
            print(f"game {i} started")
            check_states_empty( b )
            await asyncio.sleep(0.1)


    @staticmethod
    async def join_active_games():
        for i in range(10):
            b2 = Battleship()
            await b2.connect(nick=f"joiner{i}")

            set_layout( b2, get_basic_layout_1() )
            await b2.join(f"host{i}")
            check_states_empty( b2 )
            print(f"game {i} joined")
            await asyncio.sleep(0.1)

        await asyncio.sleep(1)
        raise TimeoutError #test ended


    @staticmethod
    async def waiter():
        b = Battleship()

        await b.connect(nick="infiniteLister")
        set_layout( b, get_basic_layout_1() )

        lst = await b.list_games()
        assert False, f"listed {lst}, should not list anything and wait forever"

class TestList_ActiveGames_IncreaseDecrease_TwoPlayers:

    @staticmethod
    async def launch():
        TestList_ActiveGames_IncreaseDecrease_TwoPlayers.queue = asyncio.Queue(maxsize=1)
        TestList_ActiveGames_IncreaseDecrease_TwoPlayers.sem = asyncio.Semaphore(0)
 
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestList_ActiveGames_IncreaseDecrease_TwoPlayers.add_active_games(),
                                TestList_ActiveGames_IncreaseDecrease_TwoPlayers.join_active_games(),
                                TestList_ActiveGames_IncreaseDecrease_TwoPlayers.waiter(), )


    @staticmethod
    async def add_active_games():
        ships = []
        for i in range(10):
            b = Battleship()
            ships.append( b )
            await b.connect(nick=f"host{i}")

            set_layout( b, get_basic_layout_1() )
            await b.start()
            print(f"game {i} started")
            check_states_empty( b )
            await asyncio.sleep(0.1)
            # TestList_ActiveGames_TwoPlayers.queue.add(1)

        for s in ships:
            await shoot_layout( s , get_basic_layout_1() )
            check_draw( s )
            await asyncio.sleep(0.1)


    @staticmethod
    async def join_active_games():
        ships = []
        for i in range(10):
            b2 = Battleship()
            ships.append( b2 )
            await b2.connect(nick=f"joiner{i}")

            set_layout( b2, get_basic_layout_1() )
            await b2.join(f"host{i}")
            check_states_empty( b2 )
            print(f"game {i} joined")
            await asyncio.sleep(0.1)
            # await TestList_ActiveGames_TwoPlayers.queue.get()
            # sem.release()


        for s in ships:
            await shoot_layout( s, get_basic_layout_1() )
            check_draw( s )
            await asyncio.sleep(0.1)


        # await asyncio.sleep(1)
        raise TimeoutError #test ended


    @staticmethod
    async def waiter():
        await asyncio.sleep(0.1)
        b = Battleship()

        await b.connect(nick="infiniteLister")
        set_layout( b, get_basic_layout_1() )

        # await TestList_ActiveGames_TwoPlayers.sem.acquire()
        lst = await b.list_games()
        assert False, f"listed {lst}, should not list anything and wait forever"

class TestList_WaitingGames_Increase_TwoPlayers:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   TestList_WaitingGames_Increase_TwoPlayers.add_active_games(),
                                TestList_WaitingGames_Increase_TwoPlayers.join_active_games(),
                                TestList_WaitingGames_Increase_TwoPlayers.add_additional_active_games(),
                                TestList_WaitingGames_Increase_TwoPlayers.waiter(),)


    @staticmethod
    async def add_active_games():
        for i in range(10):
            b = Battleship()
            await b.connect(nick=f"host{i}")

            set_layout( b, get_basic_layout_1() )
            await b.start()
            print(f"game {i} started")
            check_states_empty( b )
            await asyncio.sleep(0.1)


    @staticmethod
    async def join_active_games():
        for i in range(10):
            b2 = Battleship()
            await b2.connect(nick=f"joiner{i}")

            set_layout( b2, get_basic_layout_1() )
            await b2.join(f"host{i}")
            check_states_empty( b2 )
            print(f"game {i} joined")
            await asyncio.sleep(0.1)


    @staticmethod
    async def add_additional_active_games():
        for i in range(10):
            b = Battleship()
            await b.connect(nick=f"additional{i}")

            set_layout( b, get_basic_layout_1() )
            await b.start()
            print(f"additional game {i} started")
            check_states_empty( b )
            await asyncio.sleep(0.1)


    @staticmethod
    async def waiter():
        b = Battleship()

        await b.connect(nick="infiniteLister")
        set_layout( b, get_basic_layout_1() )

        for i in range(1,11):
            print("listing games")
            lst = await b.list_games()
            assert len(lst) == i, f"expected lenght {i} got {lst}"


class Test_Aisa2:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   Test_Aisa2.player_1(),
                                Test_Aisa2.player_2(), )


    @staticmethod
    async def player_1():
        b = Battleship()

        b.put_ship( 0, 0, 5, True )
        b.put_ship( 1, 0, 4, True )
        b.put_ship( 2, 0, 3, True )
        b.put_ship( 3, 0, 3, True )
        b.put_ship( 4, 0, 2, True )

        await b.connect(nick="alice")

        await b.start()
        check_states_empty( b )

        while not b.finished():
            await b.round(0, 0)

        check_lost( b )


    @staticmethod
    async def player_2():
        b = Battleship()


        b.put_ship( 0, 0, 5, True )
        b.put_ship( 1, 0, 4, True )
        b.put_ship( 2, 0, 3, True )
        b.put_ship( 3, 0, 3, True )
        b.put_ship( 4, 0, 2, True )

        await b.connect(nick="rabbit")
        await b.join( "alice" )
        check_states_empty( b )

        while not b.finished():
            await shoot_layout(b, [
                ( 0, 0, 5, True ),
                ( 1, 0, 4, True ),
                ( 2, 0, 3, True ),
                ( 3, 0, 3, True ),
                ( 4, 0, 2, True ),
            ])

        check_win( b )

class Test_Aisa:

    @staticmethod
    async def launch():
        asyncio.create_task( shipserv.start_server() )
        await asyncio.gather(   Test_Aisa.player_1(),
                                Test_Aisa.player_2(), )


    @staticmethod
    async def player_1():
        b = Battleship()

        await b.connect(nick="alice")

        b.put_ship( 0, 0, 5, True )
        b.put_ship( 1, 0, 4, True )
        b.put_ship( 2, 0, 3, True )
        b.put_ship( 3, 0, 3, True )
        b.put_ship( 4, 0, 2, True )

        await b.start()
        check_states_empty( b )

    @staticmethod
    async def player_2():
        b = Battleship()

        await b.connect(nick="rabbit")

        b.put_ship( 0, 0, 5, True )
        b.put_ship( 1, 0, 4, True )
        b.put_ship( 2, 0, 3, True )
        b.put_ship( 3, 0, 3, True )
        b.put_ship( 4, 0, 2, True )

        # await b.join( "alice" )

        check_states_empty( b )

def main():
    async def main_simple():
        await TestConnect_TwoPlayers.launch()
        await TestConnect_FourPlayers.launch()
        await TestList_TwoPlayers.launch()
        await TestWin_TwoPlayers.launch()
        await TestDraw_TwoPlayers.launch()
        await Test_Aisa.launch()
        await Test_Aisa2.launch()

        await TestWin_AutoAuto_TwoPlayers.launch()
        await TestWin_StartAuto_TwoPlayers.launch()
        await TestWin_AutoJoin_TwoPlayers.launch()

        await TestDraw_AutoAuto_TwoPlayers.launch()
        await TestDraw_AutoJoin_TwoPlayers.launch()
        await TestDraw_StartAuto_TwoPlayers.launch()

        await TestDraw_StartAuto_Restart_TwoPlayers.launch()
        await TestWin_StartAuto_Restart_TwoPlayers.launch()

        await TestWin_AutoJoin_Restart_TwoPlayers.launch()
        await TestWin_AutoAuto_Restart_TwoPlayers.launch()

        # Hash Board mismatches test
        await TestAbort_HashMismatch_StartJoin_GoodBad_TwoPlayers.launch()
        await TestAbort_HashMismatch_StartJoin_BadGood_TwoPlayers.launch()
        await TestAbort_HashMismatch_StartJoin_BadBad_Restart_TwoPlayers.launch()
        await TestAbort_BoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.launch()
        await TestAbort_HashBoardMismatch_StartJoin_BadBad_Restart_TwoPlayers.launch()

        try:
            await TestList_ActiveGames_Increase_TwoPlayers.launch()
            assert False
        except TimeoutError:
            pass

        try:
            await TestList_ActiveGames_IncreaseDecrease_TwoPlayers.launch()
            assert False
        except TimeoutError:
            pass

        await TestList_WaitingGames_Increase_TwoPlayers.launch()

        # TODO: await TestList_ActiveGames_Increase_TwoPlayers.launch()
        # TODO: await TestList_WaitingGames_TwoPlayers.launch()


    asyncio.run( main_simple() )

if __name__ == "__main__":
    main()