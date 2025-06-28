import pygame
import sys
import math
from http_client import HTTPClient
from connect_four import ConnectFour
import requests

pygame.init()
WIDTH, HEIGHT = 800, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Connect Four - Multiplayer')
FONT = pygame.font.SysFont('Segoe UI', 28, bold=True)
SMALL_FONT = pygame.font.SysFont('Segoe UI', 20)
TITLE_FONT = pygame.font.SysFont('Segoe UI', 36, bold=True)

# Enhanced color scheme
COLORS = {
    'bg': (25, 25, 45),
    'card': (45, 45, 75),
    'primary': (64, 156, 255),
    'success': (76, 217, 100),
    'warning': (255, 193, 7),
    'danger': (255, 69, 58),
    'text': (255, 255, 255),
    'text-dim': (180, 180, 200),
    'board': (35, 85, 165),
    'empty': (240, 240, 250),
    'p1': (255, 59, 48),
    'p2': (255, 204, 0)
}

# Game states
STATE_MENU, STATE_LOBBY, STATE_GAME, STATE_WIN, STATE_LOSE = 'menu', 'lobby', 'game', 'win', 'lose'

class GameClient:
    def __init__(self):
        self.state = STATE_MENU
        self.http = None
        self.player_name = ''
        self.room_id = ''
        self.lobby_players = []
        self.lobby_ready_status = {}
        self.connect4 = ConnectFour()
        self.my_idx = 0
        self.menu_notification = ""
        self.hover_col = -1
        self.animate_time = 0

    def draw_card(self, x, y, w, h, color=None):
        """Draw a card with shadow and rounded corners"""
        color = color or COLORS['card']
        # Shadow
        shadow_rect = pygame.Rect(x+3, y+3, w, h)
        pygame.draw.rect(SCREEN, (15, 15, 25), shadow_rect, border_radius=12)
        # Card
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(SCREEN, color, card_rect, border_radius=12)
        return card_rect

    def draw_button(self, x, y, w, h, text, color, hover=False):
        """Draw an enhanced button with hover effects"""
        btn_color = tuple(min(255, c + 20) for c in color) if hover else color
        btn_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(SCREEN, btn_color, btn_rect, border_radius=8)
        pygame.draw.rect(SCREEN, tuple(min(255, c + 30) for c in btn_color), btn_rect, width=2, border_radius=8)
        
        text_surf = FONT.render(text, True, COLORS['text'])
        text_x = x + (w - text_surf.get_width()) // 2
        text_y = y + (h - text_surf.get_height()) // 2
        SCREEN.blit(text_surf, (text_x, text_y))
        return btn_rect

    def draw_input_field(self, x, y, w, h, text, active=False, cursor_visible=True):
        """Draw an input field with focus states and optional blinking cursor"""
        field_color = COLORS['primary'] if active else COLORS['card']
        field_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(SCREEN, field_color, field_rect, border_radius=6)
        pygame.draw.rect(SCREEN, COLORS['text'], field_rect, width=2, border_radius=6)
        # Draw text
        text_surf = SMALL_FONT.render(text, True, COLORS['text'])
        text_x = x + 12
        text_y = y + (h - text_surf.get_height()) // 2
        SCREEN.blit(text_surf, (text_x, text_y))
        # Draw blinking cursor if active
        if active and cursor_visible:
            cursor_x = text_x + text_surf.get_width() + 2
            cursor_y = text_y
            cursor_h = text_surf.get_height()
            pygame.draw.rect(SCREEN, COLORS['text'], (cursor_x, cursor_y, 2, cursor_h))
        return field_rect

    def draw_menu(self, input_active=False, code_input_active=False, cursor_visible=True):
        SCREEN.fill(COLORS['bg'])
        
        # Title with glow effect
        title = TITLE_FONT.render('CONNECT FOUR', True, COLORS['primary'])
        subtitle = SMALL_FONT.render('Multiplayer Edition', True, COLORS['text-dim'])
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        SCREEN.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 95))
        
        # Main card
        card_w, card_h = 400, 450
        card_x = (WIDTH - card_w) // 2
        card_y = 140
        self.draw_card(card_x, card_y, card_w, card_h)
        
        # Name input
        name_label = SMALL_FONT.render('Player Name:', True, COLORS['text'])
        SCREEN.blit(name_label, (card_x + 30, card_y + 40))
        name_box = self.draw_input_field(card_x + 30, card_y + 70, card_w - 60, 40, self.player_name, active=input_active, cursor_visible=cursor_visible)
        
        # Room code input
        room_label = SMALL_FONT.render('Room Code (optional):', True, COLORS['text'])
        SCREEN.blit(room_label, (card_x + 30, card_y + 140))
        code_box = self.draw_input_field(card_x + 30, card_y + 170, card_w - 60, 40, self.room_id, active=code_input_active, cursor_visible=cursor_visible)
        
        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        btn_w, btn_h = card_w - 60, 50
        btn_x = card_x + 30
        
        btn_create = self.draw_button(btn_x, card_y + 240, btn_w, btn_h, 'Create Room', COLORS['primary'],
                                    pygame.Rect(btn_x, card_y + 240, btn_w, btn_h).collidepoint(mouse_pos))
        btn_quick = self.draw_button(btn_x, card_y + 310, btn_w, btn_h, 'Quick Join', COLORS['success'],
                                   pygame.Rect(btn_x, card_y + 310, btn_w, btn_h).collidepoint(mouse_pos))
        btn_join = self.draw_button(btn_x, card_y + 380, btn_w, btn_h, 'Join with Code', COLORS['warning'],
                                  pygame.Rect(btn_x, card_y + 380, btn_w, btn_h).collidepoint(mouse_pos))
        
        # Notification
        if self.menu_notification:
            notif = SMALL_FONT.render(self.menu_notification, True, COLORS['danger'])
            SCREEN.blit(notif, (WIDTH//2 - notif.get_width()//2, card_y + card_h + 20))
        
        return name_box, btn_create, btn_quick, btn_join, code_box

    def draw_lobby(self):
        SCREEN.fill(COLORS['bg'])
        
        # Title
        title = TITLE_FONT.render(f'Room: {self.room_id}', True, COLORS['primary'])
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Players card
        card_w, card_h = 500, 300
        card_x = (WIDTH - card_w) // 2
        card_y = 150
        self.draw_card(card_x, card_y, card_w, card_h)
        
        # Players list
        players_title = FONT.render('Players', True, COLORS['text'])
        SCREEN.blit(players_title, (card_x + 30, card_y + 30))
        
        y_offset = 80
        for i, player in enumerate(self.lobby_players):
            ready = self.lobby_ready_status.get(player, False)
            # Player indicator
            indicator_color = COLORS['success'] if ready else COLORS['warning']
            pygame.draw.circle(SCREEN, indicator_color, (card_x + 50, card_y + y_offset + 15), 8)
            
            # Player name
            name_text = SMALL_FONT.render(player, True, COLORS['text'])
            SCREEN.blit(name_text, (card_x + 80, card_y + y_offset))
            
            # Status
            status_text = SMALL_FONT.render('Ready' if ready else 'Waiting...', True, indicator_color)
            SCREEN.blit(status_text, (card_x + card_w - 130, card_y + y_offset))
            
            y_offset += 50
        
        # Ready button
        mouse_pos = pygame.mouse.get_pos()
        btn_ready = self.draw_button(card_x + 30, card_y + card_h - 80, card_w - 60, 50, 
                                   'READY!', COLORS['success'],
                                   pygame.Rect(card_x + 30, card_y + card_h - 80, card_w - 60, 50).collidepoint(mouse_pos))
        
        return btn_ready

    def draw_board(self, board, grid_top=120):
        """Enhanced board with hover effects and animations"""
        grid_left = (WIDTH - 7*80) // 2
        cell_size = 80
        
        # Board background with gradient effect
        board_rect = pygame.Rect(grid_left - 15, grid_top - 15, 7*cell_size + 30, 6*cell_size + 30)
        pygame.draw.rect(SCREEN, COLORS['board'], board_rect, border_radius=15)
        
        # Column hover effect
        if 0 <= self.hover_col < 7:
            hover_rect = pygame.Rect(grid_left + self.hover_col*cell_size - 5, grid_top - 5, cell_size + 10, 6*cell_size + 10)
            pygame.draw.rect(SCREEN, tuple(min(255, c + 20) for c in COLORS['board']), hover_rect, border_radius=8)
        
        # Draw pieces with enhanced visuals
        for r in range(6):
            for c in range(7):
                center = (grid_left + c*cell_size + cell_size//2, grid_top + r*cell_size + cell_size//2)
                
                if board[r][c] == 0:  # Empty
                    pygame.draw.circle(SCREEN, COLORS['empty'], center, cell_size//2 - 8)
                    pygame.draw.circle(SCREEN, COLORS['board'], center, cell_size//2 - 8, 3)
                else:
                    # Player pieces with shine effect
                    piece_color = COLORS['p1'] if board[r][c] == 1 else COLORS['p2']
                    pygame.draw.circle(SCREEN, piece_color, center, cell_size//2 - 6)
                    # Shine effect
                    shine_center = (center[0] - 8, center[1] - 8)
                    pygame.draw.circle(SCREEN, tuple(min(255, c + 80) for c in piece_color), shine_center, 12)

    def draw_game(self, board, turn, my_turn, player_names=None):
        SCREEN.fill(COLORS['bg'])
        
        # Top info bar
        bar_height = 80
        bar_rect = pygame.Rect(0, 0, WIDTH, bar_height)
        pygame.draw.rect(SCREEN, COLORS['card'], bar_rect)
        
        # Turn indicator with animation
        self.animate_time += 1
        pulse = int(20 * (1 + math.sin(self.animate_time * 0.1)))
        
        if player_names and len(player_names) == 2:
            current_player = player_names[turn]
            turn_text = f"Turn: {current_player}"
        else:
            turn_text = "Your Turn!" if my_turn else "Opponent's Turn"
        
        turn_color = tuple(min(255, c + pulse) for c in (COLORS['success'] if my_turn else COLORS['text-dim']))
        turn_surf = FONT.render(turn_text, True, turn_color)
        SCREEN.blit(turn_surf, (WIDTH//2 - turn_surf.get_width()//2, bar_height//2 - turn_surf.get_height()//2))
        
        # Draw board
        self.draw_board(board, grid_top=bar_height + 20)
        
        # Player info at bottom
        if player_names and len(player_names) == 2:
            p1_text = SMALL_FONT.render(f"● {player_names[0]}", True, COLORS['p1'])
            p2_text = SMALL_FONT.render(f"● {player_names[1]}", True, COLORS['p2'])
            SCREEN.blit(p1_text, (50, HEIGHT - 50))
            SCREEN.blit(p2_text, (WIDTH - p2_text.get_width() - 50, HEIGHT - 50))

    def draw_end_screen(self, won):
        SCREEN.fill(COLORS['bg'])
        
        # Result card
        card_w, card_h = 400, 300
        card_x, card_y = (WIDTH - card_w) // 2, (HEIGHT - card_h) // 2
        result_color = COLORS['success'] if won else COLORS['danger']
        self.draw_card(card_x, card_y, card_w, card_h, result_color)
        
        # Result text with animation
        result_text = "VICTORY!" if won else "DEFEAT"
        text_surf = TITLE_FONT.render(result_text, True, COLORS['text'])
        SCREEN.blit(text_surf, (card_x + (card_w - text_surf.get_width()) // 2, card_y + 60))
        
        # Menu button
        mouse_pos = pygame.mouse.get_pos()
        btn_menu = self.draw_button(card_x + 100, card_y + 180, 200, 50, 'Return to Menu', COLORS['primary'],
                                  pygame.Rect(card_x + 100, card_y + 180, 200, 50).collidepoint(mouse_pos))
        return btn_menu

    def run(self):
        clock = pygame.time.Clock()
        input_active = code_input_active = False
        last_game_state_poll = 0
        cached_game_state = None
        poll_interval_ms = 200  # 200ms
        cursor_timer = 0
        cursor_visible = True
        # --- Add lobby polling timer and cache ---
        last_lobby_poll = 0
        cached_lobby = None
        while True:
            mouse_pos = pygame.mouse.get_pos()
            dt = clock.tick(60)
            cursor_timer += dt
            if cursor_timer > 500:
                cursor_visible = not cursor_visible
                cursor_timer = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.state == STATE_MENU:
                    name_box, btn_create, btn_quick, btn_join, code_box = self.draw_menu(input_active, code_input_active, cursor_visible)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        input_active = name_box.collidepoint(event.pos)
                        code_input_active = code_box.collidepoint(event.pos)
                        if not (input_active or code_input_active):
                            input_active = code_input_active = False
                        # --- Create Room ---
                        if btn_create.collidepoint(event.pos) and self.player_name:
                            self.menu_notification = ""
                            self.http = HTTPClient(self.player_name)
                            data = self.http.create_room()
                            self.room_id = data['room_id']
                            self.state = STATE_LOBBY
                        # --- Quick Join ---
                        elif btn_quick.collidepoint(event.pos) and self.player_name:
                            self.menu_notification = ""
                            self.http = HTTPClient(self.player_name)
                            data = self.http.quick_join()
                            self.room_id = data['room_id']
                            self.state = STATE_LOBBY
                        # --- Join with Code ---
                        elif btn_join.collidepoint(event.pos) and self.player_name and self.room_id:
                            self.menu_notification = ""
                            self.http = HTTPClient(self.player_name)
                            try:
                                data = self.http.join_room(self.room_id)
                                self.room_id = data['room_id']
                                self.state = STATE_LOBBY
                            except:
                                self.menu_notification = "Failed to join room"
                                
                    elif event.type == pygame.KEYDOWN:
                        if input_active:
                            if event.key == pygame.K_BACKSPACE:
                                self.player_name = self.player_name[:-1]
                            elif len(self.player_name) < 16 and event.unicode.isprintable():
                                self.player_name += event.unicode
                        elif code_input_active:
                            if event.key == pygame.K_BACKSPACE:
                                self.room_id = self.room_id[:-1]
                            elif len(self.room_id) < 16 and event.unicode.isprintable():
                                self.room_id += event.unicode
                elif self.state == STATE_LOBBY:
                    btn_ready = self.draw_lobby()
                    if event.type == pygame.MOUSEBUTTONDOWN and btn_ready.collidepoint(event.pos) and self.http:
                        self.http.set_ready()
                        cached_lobby = None  # force refresh after ready
                    # Poll lobby status only every poll_interval_ms
                    now = pygame.time.get_ticks()
                    if self.http and (cached_lobby is None or now - last_lobby_poll > poll_interval_ms):
                        cached_lobby = self.http.lobby_status()
                        last_lobby_poll = now
                    lobby = cached_lobby or {'players': [], 'ready': {}}
                    self.lobby_players = lobby.get('players', [])
                    self.lobby_ready_status = lobby.get('ready', {})
                    if len(self.lobby_players) == 2 and all(self.lobby_ready_status.values()):
                        self.my_idx = self.lobby_players.index(self.player_name)
                        self.state = STATE_GAME
                        self.connect4.reset()
                        cached_game_state = None
                        cached_lobby = None
                elif self.state == STATE_GAME:
                    # Update hover column (always, for smooth UI)
                    grid_left = (WIDTH - 7*80) // 2
                    if grid_left <= mouse_pos[0] < grid_left + 7*80:
                        self.hover_col = (mouse_pos[0] - grid_left) // 80
                    else:
                        self.hover_col = -1
                    # Poll game state only every poll_interval_ms
                    now = pygame.time.get_ticks()
                    if self.http and (cached_game_state is None or now - last_game_state_poll > poll_interval_ms):
                        cached_game_state = self.http.game_state()
                        last_game_state_poll = now
                    state = cached_game_state or {'board': [[0]*7 for _ in range(6)], 'turn': 0, 'winner': None}
                    board = state.get('board', [[0]*7 for _ in range(6)])
                    turn = state.get('turn', 0)
                    winner = state.get('winner', None)
                    my_turn = (turn == self.my_idx)
                    self.draw_game(board, turn, my_turn, self.lobby_players)
                    if winner:
                        self.state = STATE_WIN if winner == self.player_name else STATE_LOSE
                        cached_game_state = None
                    elif event.type == pygame.MOUSEBUTTONDOWN and my_turn and 0 <= self.hover_col < 7:
                        if self.http is not None:
                            self.http.make_move(self.hover_col)
                            cached_game_state = None  # force refresh after move
                elif self.state in [STATE_WIN, STATE_LOSE]:
                    btn_menu = self.draw_end_screen(self.state == STATE_WIN)
                    if event.type == pygame.MOUSEBUTTONDOWN and btn_menu.collidepoint(event.pos):
                        self.__init__()  # Reset game state
                        
            if self.state not in [STATE_GAME]:
                pygame.display.flip()
            else:
                pygame.display.flip()
            clock.tick(60)

if __name__ == '__main__':
    GameClient().run()
