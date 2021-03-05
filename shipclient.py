# The client API.

import asyncio
from common import parse as hw3_parse
from shipserv import _SOCKET_NAME
from typing import List, Dict
import common
from common import _SHIPS_HEALTH, _SOCKET_NAME

async def check_line( reader, expect ):
    expect += '\n'
    got = await reader.readline()
    assert got.decode() == f"{expect}", f"{got} == {expect}"

class Battleship:

    def __init__(self):
        self._reader = None
        self._writer = None
        self._salt = common.generate_salt()
        self._server_salt = None

        self._ship_layout = []
        self._ships = [['w' for _ in range(10)] for _ in range(10)]
        self._enemy_ships = [['?' for _ in range(10)] for _ in range(10)]

        self._hash = None
        self._game_id = None
        self._available_games = None

        self._put_ship_called = 0

        self._end_status = None # either "win" "draw" "lose" or "abort"
        self._end_mismatch = None
        self._early_end = None

        self._hit_count = 0
        self._enemy_hit_count = 0
        self._is_host = False

    async def _send_command( self, msg ):
        self._writer.write( msg.encode() )
        await self._writer.drain()

    async def _get_server_response( self ):
        data = await self._reader.readline()
        return hw3_parse( data.decode() )

    async def connect( self, nick: str ):
        self._nick = nick

        r, w = await asyncio.open_unix_connection( _SOCKET_NAME )
        self._reader = r
        self._writer = w

        await self._send_command( f'(nick "{nick}" "{self._salt}")' )

        status = await self._get_server_response()
        assert status[0] == "ok"
        assert status[1].is_string() #TODO remove
        self._server_salt = str( status[1] )

    def _get_layout_for_hash( self ):
        layout = sorted( self._ship_layout, key=lambda x: (x[0], x[1], x[2]), reverse=True )
        return[ (t[1], t[2], t[3]) for t in layout ]

    def put_ship( self, x: int, y: int, size: int, vertical: bool ):
        #  • ‹put_ship( x, y, size, vertical )› puts a ship of a given size at
        #    position x, y where x is the column and y is the row, with (0, 0)
        #    being the upper left corner; if ‹vertical› is True, then the ship
        #    extends downwards, and if it is False, it extends to the right
        #    ... this method must be called exactly 5 times before ‹start()›
        #    or ‹join()› are called, with sizes 5, 4, 3, 3, 2 (in any order)
        self._ship_layout.append( (size, x, y, vertical) ) # TODO add check for correct layout
        for i in range(size):
            if vertical:
                assert y+i < 10 # TODO change so that user can fix himself
                assert self._ships[y+i][x] == 'w' # TODO remove
                self._ships[y+i][x] = 's'
            else:
                assert x+i < 10 # TODO change so that user can fix himself
                assert self._ships[y][x+i] == 'w' # TODO remove
                self._ships[y][x+i] = 's'

        self._put_ship_called += 1


    async def start( self ):
        """Announces a new game on the server and waits for the second player to join."""
        assert self._put_ship_called == 5 # TODO remove

        self._hash = common.hash_game( self._server_salt, self._salt, self._get_layout_for_hash() )

        await self._send_command( f'(start "{self._hash}")' )
        response = await self._get_server_response()
        assert response[0] == 'started' # TODO remove
        self._game_id = int(response[1])

        self._is_host = True
        # # wait until someone joins
        # joined = await self._get_server_response()
        # assert joined[0] == "game" and joined[1] == "started" # TODO remove


    async def _get_games( self ):
        """Request server and return the buffered result."""
        await self._send_command( f'(list)' )

        games = None
        while True: # parsing and waiting for all the lines to be received
            games = await self._get_server_response()
            if games:
                if len(games) == 1: # TODO consider server side holding, not client's
                    await self._send_command( f'(list)' )
                else:
                    return games
            await asyncio.sleep(0.1)

    async def list_games( self ) -> List[ str ]:
        """Return a list of nicks who announced a game and are waiting for other player.

           Each subsequent call blocks until the list changes since the last
           call; never returns an empty list (i.e. blocks until it can
           return a non-empty list)
        """
        server_resp = await self._get_games()
        server_list = server_resp[1:]
        games: Dict[str, List[int]]= { str(g[1]):[] for g in server_list if g[0] == "waiting" }

        if len(games) == 0 or self._available_games:
            while True:
                if len(games) == 0:
                    pass
                elif self._available_games != games: # TODO should compare sets of nicks instead responses
                    break

                await asyncio.sleep(0.1) # TODO is this correct?
                server_resp = await self._get_games()
                server_list = server_resp[1:]
                games = { str(g[1]):[] for g in server_list if g[0] == "waiting" }

        self._available_games = games
        return [ nick for nick in games ]


    async def auto( self ):
        """Join random game or create a new one."""
        assert self._put_ship_called == 5 # TODO remove

        self._hash = common.hash_game( self._server_salt, self._salt, self._get_layout_for_hash() )

        await self._send_command( f'(auto "{self._hash}")' )
        resp = await self._get_server_response()

        assert len(resp) == 2 or len(resp) == 3 #TODO remove
        self._game_id = resp[1]

        if str(resp) == f"(started {self._game_id})":
            self._is_host = True
        elif str(resp) == f"(game {self._game_id} joined)": #TODO remove
            pass
        else:
            assert False  #TODO remove


    async def join( self, nick: str ):
        """Join a game announced by ‹nick›."""
        assert self._put_ship_called == 5 # TODO remove

        self._hash = common.hash_game( self._server_salt, self._salt, self._get_layout_for_hash() )

        await self._send_command( f'(joinplayer "{nick}" "{self._hash}")' )
        resp = await self._get_server_response()
        self._game_id = int(resp[1])
        assert str(resp) == f"(game {self._game_id} joined)" #TODO remove


    def enemy( self ) -> List[ List[ str ] ]:
        """Return the state of the enemy board.

        Cells encoded as 'h' for hit, 'm' for miss and '?' for unknown
        """
        return self._enemy_ships


    def board( self ) -> List[ List[ str ] ]:
        """Return player's own board.

        Cell might be 'w' for water or 's' for ship."""
        return self._ships


    async def _process_received_attack( self, attack ):
        """Record damgage end return result."""
        x = int( attack[2] )
        y = int( attack[3] )

        damage = None
        if self._ships[y][x] == "s":
            self._ships[y][x] = "h"
            self._hit_count += 1
            damage = "hit"
        else:
            if self._ships[y][x] != "h":
                self._ships[y][x] = "m"
            damage = "miss"

        await self._send_command( f'({damage} {self._game_id})' )


    async def _send_layout_to_server( self ):
        """ (layout 123 (ship 5 0 0 horizontal)
                   (ship 4 5 5 vertical)
                   (ship 3 6 5 vertical)
                   (ship 3 8 5 vertical)
                   (ship 2 9 9 horizontal)). """
        ships = []
        for size,x,y,vertical in self._ship_layout:
            align = "vertical" if vertical else "horizontal"
            ships.append(f"(ship {size} {x} {y} {align})")

        ships_msg = " ".join(ships) # TODO "/n" join or " "
        msg = f"(layout {self._game_id} {ships_msg})"
        await self._send_command( msg )


    async def _process_game_end( self ):
        """Call when end of game occured."""
        if not self._early_end:
            self._early_end = await self._get_server_response()
        end_response = self._early_end
        assert end_response[0] == "end" # TODO remove
        winner = str(end_response[2])

        await self._send_layout_to_server()

        game_status = await self._get_server_response()

        is_draw = False
        if game_status[0] == "end":
            is_draw = True
            game_status = await self._get_server_response()

        if game_status[1] == "aborted":
            self._end_mismatch = await self._get_server_response()
            self._end_status = "abort"

        elif game_status[1] == "ok":
            self._end_status =  "d" if is_draw else \
                                "w" if winner == self._nick else \
                                "l" 

        else:
            assert False #TODO remove


    async def round( self, x, y ):
        """Play one round, shooting at ‹(x, y)›."""
        if self._is_host:
            resp = await self._get_server_response()
            assert str(resp) == f'(game {self._game_id} joined)' #TODO remove
            self._is_host = False

        await self._send_command( f'(shoot {self._game_id} {x} {y})' )
        attack = await self._get_server_response()
        await self._process_received_attack( attack )

        result = await self._get_server_response()

        if result[0] == "hit" or result[0] == "miss":
            self._enemy_ships[y][x] = "h" if result[0] == "hit" else "m"
            if result[0] == "hit":
                self._enemy_hit_count += 1
        elif result[0] == "end":
            self._early_end = result
            result = await self._get_server_response()
            if result[0] == "hit" or result[0] == "miss":
                self._enemy_ships[y][x] = "h" if result[0] == "hit" else "m"
            if result[0] == "hit":
                self._enemy_hit_count += 1


        if self._hit_count == _SHIPS_HEALTH or self._enemy_hit_count == _SHIPS_HEALTH:
            await self._process_game_end()


    def finished( self ) -> bool:
        return self._end_status is not None

    def won( self ) -> bool:
        return self._end_status == "w"

    def draw( self ) -> bool:
        return self._end_status == "d"

    def aborted( self ) -> bool:
        return self._end_status == "abort"

    def restart( self ):
        self._ship_layout = []
        self._ships = [['w' for _ in range(10)] for _ in range(10)]
        self._enemy_ships = [['?' for _ in range(10)] for _ in range(10)]

        self._hash = None
        self._game_id = None
        self._available_games = None

        self._put_ship_called = 0

        self._end_status = None # either "win" "draw" "lose" or "abort"
        self._end_mismatch = None
        self._early_end = None

        self._hit_count = 0
        self._enemy_hit_count = 0
        self._is_host = False