# Implement the server here.

import asyncio
import os
import time
from asyncio import Event, IncompleteReadError
from os.path import join
from pathlib import Path
from typing import List, Optional
import common

from common import parse as hw3_parse
from common import _SOCKET_NAME, _SHIPS_HEALTH

class ServerError(Exception):
    pass

class UnknownCommand(ServerError):
    pass

class InvalidExpression(ServerError):
    pass

class LoginError(ServerError):
    pass

class Server:
    def __init__(self):
        self.players = {}
        # { player_writer:
        #   {
        #       "nick": <nick>,
        #       "salt": <salt>
        #   }
        # }
        self.games = {}
        # { game_id: 
        #   {
        #       p1_writer:
        #       {
        #           "hash": <hashed_layout>,
        #           "hits": <hit_count>,
        #       }
        #       p2_writer:
        #       ...
        #   }
        # }
        self.game_turns = {}
        # { game_id: player }
        self._inner_id_counter = 1

        self._new_game_event = Event()

    @staticmethod
    def check_string_literal(command):
        if not command.is_string():
            raise UnknownCommand("String must be encapsulated in double quotes")

    @staticmethod
    def check_command_length(command, length):
        if len(command) != length:
            raise InvalidExpression(f"Expected {command[0]} command in invalid format")

    def check_player( self, player ):
        if player not in self.players:
            raise ServerError("Player does not exist.")

    def check_game( self, game_id ):
        if game_id not in self.games:
            raise ServerError(f"Game {game_id} does not exist.")

    def check_player_and_game( self, player, game_id ):
        self.check_player( player )
        self.check_game( game_id )


    async def _send_to_player( self, player, command ):
        player.write( f'{ str(command) }\n'.encode() )
        await player.drain()

    async def _send_lines_to_player( self, player, command ):
        player.write( f'{ str(command) }\n'.encode() )
        await player.drain()


    async def _nick( self, player, command ):
        """ (nick "foo" "salt") """
        Server.check_command_length( command, 3 )

        Server.check_string_literal( command[1] )
        nick = str(command[1])

        Server.check_string_literal( command[2] )
        salt = str(command[2])

        if not nick.isalnum():
            raise InvalidExpression("Login nick not alphanumeric")

        for p,attributes in self.players.items():
            if attributes["nick"] == nick and player != p:
                raise LoginError("Nick already in use")

        server_salt = common.generate_salt()

        self.players[ player ] = {
            "nick": nick,
            "salt": salt,
            "server_salt": server_salt,
        }

        await self._send_to_player( player, f'(ok "{server_salt}")' )


    async def _join( self, player, command ):
        """ (join 123 "hash") """
        Server.check_command_length( command, 3 )
        game_id = int(command[1])
        hashed = str(command[2])

        if game_id not in self.games:
            raise LoginError("Game does not exist.")

        game = self.games[game_id]
        if len(game) >= 2:
            raise LoginError("Cannot join, game active.")

        self.games[game_id][player] = {
                "hash": hashed,
                "hits": 0,
                "layout": None,
                "turn": None,
                "cached_ships": [['?' for _ in range(10)] for _ in range(10)],
            }

        other_player = self._get_other_player( game_id, player )
        await self._send_to_player( player, f'(game {game_id} joined)')
        await self._send_to_player( other_player, f'(game {game_id} joined)')


    def _get_id_counter( self ):
        game_id = self._inner_id_counter
        self._inner_id_counter += 1
        return game_id


    async def _start( self, player, command ):
        """ (start "hash") """
        Server.check_command_length( command, 2 )

        if player not in self.players: # TODO ask if server will be standalone tested or not (with just battleship)
            raise LoginError("Player must be logged before starting a game")

        hashed = str(command[1])

        game_id = self._get_id_counter()

        assert game_id not in self.games #TODO remove
        self.games[game_id] = {
            player : {
                "hash": hashed,
                "hits": 0,
                "layout": None,
                "turn": None,
                "cached_ships": [['?' for _ in range(10)] for _ in range(10)],
            }
        }

        await self._send_to_player( player, f'(started {game_id})')



    def _get_all_games( self ) -> List[str]:
        games = []
        for g in self.games:
            players = list(self.games[g])
            if len(players) == 1:
                games.append( f'(waiting "{self.players[ players[0] ]["nick"]}" {g})' )
            elif len(players) == 2:
                games.append( f'(active "{self.players[ players[0] ]["nick"]}" "{self.players[ players[1] ]["nick"]}" {g})' )
            else:
                assert False #TODO remove
        return games


    async def _list( self, player ):
        """ (list) """
        games = " ".join(self._get_all_games())

        await self._send_to_player( player, f'(games {games})' )


    def _get_other_player( self, game_id, player ) -> asyncio.StreamWriter:
        other_player = None
        for p in self.games[game_id]:
            if player != p:
                other_player = p
                break
        assert other_player #TODO remove
        return other_player


    async def _shoot( self, player, command ):
        """ (shoot <game_id> <col> <row> ) """
        Server.check_command_length( command, 4 )
        game_id = int(command[1])
        col = int(command[2])
        row = int(command[3])

        assert col < 10 and row < 10 # TODO remove
        assert game_id in self.games # TODO remove

        other_player = self._get_other_player( game_id, player )

        if not other_player:
            raise LoginError("Game not started")

        if self.games[game_id][player]["turn"] is not None:
            raise ServerError("Cannot shoot two times in row!")

        self.games[game_id][player]["turn"] = [col, row]
        await self._send_to_player(other_player, f"(shoot {game_id} {col} {row})")


    async def _hit_or_miss( self, player, command ):
        Server.check_command_length( command, 2 )
        identifier = command[0]
        game_id = int(command[1])

        #TODO check other player and game
        other = self._get_other_player( game_id=game_id, player=player )

        game = self.games[game_id]

        await self._send_to_player( other, command )

        x,y = game[other]["turn"]
        board = game[other]["cached_ships"]
        if identifier == "hit":
            board[y][x] = "h"
        elif identifier == "miss":
            if board[y][x] == "?":
                board[y][x] == "m"

        game[other]["turn"] = None

        if identifier == "hit":
            game[other]["hits"] += 1

            if game[other]["hits"] == _SHIPS_HEALTH:
                winner_nick = self.players[other]["nick"]
                winner_message = f'(end {game_id} "{winner_nick}")' 
                await self._send_to_player( player, winner_message )
                await self._send_to_player( other, winner_message )

                #TODO should I set flag? error handling in case of invalid layout sending
                # not described


    def _verify_hash( self, player, game_id ) -> bool:
        game = self.games[game_id]

        player_salt = self.players[player]["salt"]
        player_server_salt = self.players[player]["server_salt"]
        player_hash = game[player]["hash"]

        layout = game[player]["layout"]
        player_layout = [ (t[1], t[2], t[3] == "vertical") for t in layout ]

        calculated_hash = common.hash_game(player_server_salt, player_salt, player_layout)

        return calculated_hash == player_hash

    def _verify_board( self, player, game_id ) -> bool:
        player_layout = self.games[game_id][player]["layout"]
        cached_board = self.games[game_id][player]["cached_ships"]
        nick = self.players[player]["nick"]

        player_board = [['w' for _ in range(10)] for _ in range(10)]
        # ship in shape (size, x, y, vertical||horizontal)
        for size,x,y,direction in player_layout:
            for i in range(size):
                if direction == "horizontal":
                    player_board[y][x+i] = 's'
                else:
                    player_board[y+i][x] = 's'

        for x in range(10):
            for y in range(10):
                if cached_board[y][x] == 'h':
                    if player_board[y][x] != 's':
                        return False
                elif cached_board[y][x] == 'm':
                    if player_board[y][x] != 'w':
                        return False

        return True


    async def _verify( self, player, game_id ):
        other_player = self._get_other_player( game_id, player )

        player_nick = self.players[player]["nick"]
        other_player_nick = self.players[player]["nick"]

        p1_hash = self._verify_hash( player, game_id )
        p2_hash = self._verify_hash( other_player, game_id )

        p1_board = self._verify_board( player, game_id )
        p2_board = self._verify_board( other_player, game_id )

        if p1_hash and p2_hash and p1_board and p2_board:
            await self._send_to_player( player, f'(game ok)' )
            await self._send_to_player( other_player, f'(game ok)')
            return
        
        await self._send_to_player( player, f'(game aborted)' )
        await self._send_to_player( other_player, f'(game aborted)' )

        mismatch_message = ""
        if not p1_hash:
            mismatch_message += f'(hash-mismatch {game_id} {player_nick})'

        if not p2_hash:
            mismatch_message += f'(hash-mismatch {game_id} {other_player_nick})'

        if not p1_board:
            mismatch_message += f'(board-mismatch {game_id} {player_nick})'

        if not p2_board:
            mismatch_message += f'(board-mismatch {game_id} {other_player_nick})'

        await self._send_to_player( player, mismatch_message )
        await self._send_to_player( other_player, mismatch_message )

    def _remove_game( self, game_id: int ):
        """Remove game from server."""
        self.games.pop( game_id )

    async def _layout( self, player, command ):
        #   (layout 123 (ship 5 0 0 horizontal)
        #                 (ship 4 5 5 vertical)
        #                 (ship 3 6 5 vertical)
        #                 (ship 3 8 5 vertical)
        #                 (ship 2 9 9 horizontal))
            
        #     the order of ships is mandatory, the first argument is the size
        #     of the ship and the other two numbers are the x and y
        #     coordinates of the top/left square of the ship; 
        Server.check_command_length( command, 7 )

        game_id = int(command[1])

        # TODO handle invalid layout ?
        ships = command[2:]
        layout = [ [ int(s[1]), int(s[2]), int(s[3]), s[4] ] for s in ships  ]
        layout = sorted(layout, key=lambda x: (x[0], x[1], x[2]), reverse=True)

        game = self.games[game_id]
        assert game_id in self.games #TODO remove
        game[player]["layout"] = layout

        other_player = self._get_other_player( game_id, player )

        if game[other_player]["layout"]:
            await self._verify(player, game_id)
            self._remove_game( game_id )


    def _get_active_game( self, player = None ) -> Optional[int]:
        """Get active game for a player. 

        If player not specified, get random active game
        """
        for g_id in self.games:
            players = list(self.games[g_id])
            if len(players) == 1:
                if player:
                    if player == players[0]:
                        return g_id
                else:
                    return g_id
        return None

    #     wait_task = asyncio.create_task( await self._new_game_event.wait() )
    #     await wait_task
    #     return self._get_active_game( nick=nick )

    async def _auto( self, player, command ):
        # (auto "hash")
        Server.check_command_length( command, 2 )
        hashed = str(command[1]) # TODO remove string trimming

        game_id = self._get_active_game()
        if not game_id:
            await self._start( player, hw3_parse(f'(start "{hashed}")') )
        else:
            await self._join( player, command=hw3_parse(f'(join {game_id} "{hashed}")') )

    async def _joinplayer( self, player, command ):
        """
        request:    (joinplayer "nick" "hash")
        response:   (game <id> joined)
        """
        Server.check_command_length( command, 3 )
        nick = str(command[1])
        hashed = str(command[2]) # TODO remove string trimming

        other_player = None
        for p in self.players:
            if self.players[p]["nick"] == nick:
                other_player = p
                break

        if not other_player:
            raise UnknownCommand(f'(error "Player {nick} not found"')

        found = self._get_active_game( other_player )
        if not found:
            raise UnknownCommand(f'(error "Player {nick} has not started game yet")')

        await self._join( player, command=hw3_parse(f'(join {found} "{hashed}")') )


    async def execute(self, command, player):
        identifier = command[0]

        if identifier == "nick":
            await self._nick( player, command )

        elif identifier == "start":
            await self._start( player, command )

        elif identifier == "join":
            await self._join( player, command )

        elif identifier == "list":
            await self._list( player )

        elif identifier == "shoot":
            await self._shoot( player, command )

        elif identifier == "hit" or identifier == "miss":
            await self._hit_or_miss( player, command )

        elif identifier == "auto":
            await self._auto( player, command )

        elif identifier == "joinplayer":
            await self._joinplayer( player, command )

        elif identifier == "layout":
            await self._layout( player, command )

        else:
            raise UnknownCommand("Command not known.")


    # def sign_out_user(self, peer):
    #     if peer not in self.users:
    #         return

    #     for ch in self.channels_users:
    #         if peer in self.channels_users[ch]:
    #             self.channels_users[ch].remove(peer)


    async def handle_client(self, reader, writer):
        first_command = True

        buffer = ""
        while True:
            try:
                data = await reader.readexactly(1)
            except IncompleteReadError:
                # self.sign_out_user(writer)
                break

            buffer += data.decode()
            command = hw3_parse( buffer )

            if command is None:
                continue

            try:

                if first_command:
                    if command[0] != "nick":
                        raise LoginError("Login first required")
                    
                    try:
                        await self.execute(player=writer, command=command)
                        first_command = False
                    except ServerError as e:
                        raise e
                else:
                    await self.execute(command=command, player=writer)

            except ServerError as e:
                error = f'(error "{str(e)}")\n'
                writer.write(error.encode())
                await writer.drain()

            buffer = ""


async def start_server():
    path = Path(os.getcwd()).joinpath(_SOCKET_NAME)

    if os.path.isfile(path):
        os.remove(path)

    server = Server()
    s = await asyncio.start_unix_server(server.handle_client, path=path)
    await s.serve_forever() #TODO uncomment after testing


def main():
    async def main_simple():
        await start_server()

    asyncio.run( main_simple() )

if __name__ == "__main__":
    main()