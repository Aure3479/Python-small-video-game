import pygame
import csv
import random
import time
from datetime import datetime
import librosa
import threading
import os
import serial  # For serial communication with Arduino

# --- Configuration ---

# Serial port configuration for Arduino
SERIAL_PORT = 'COM3'  # Replace with your Arduino's serial port
BAUD_RATE = 115200

# Initialize serial communication
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.write(b"Hello from Python!\n")
    answer = ser.readline()
    print(answer.decode())
    print("connection made on ",SERIAL_PORT," with a Baud rate of ", BAUD_RATE)
except serial.SerialException:
    ser = None
    print("Arduino not connected. Serial inputs will be ignored.")

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rhythm Game: Directional Defense")
clock = pygame.time.Clock()

# Colors and font
WHITE = (255, 255, 255)
FONT = pygame.font.Font(None, 36)

# --- Classes ---

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.size = 20
        self.color = (0, 0, 0)  # Color not used as we display a sprite
        self.image = None  # To be loaded in Game class

class Enemy:
    def __init__(self, direction, speed, image):
        self.direction = direction
        self.speed = speed
        self.active = True
        self.image = image
        if direction == 'up':
            self.x = WIDTH //2
            self.y = 0
        elif direction == 'down':
            self.x = WIDTH //2
            self.y = HEIGHT
        elif direction == 'left':
            self.x = 0
            self.y =  HEIGHT //2
        elif direction == 'right':
            self.x = WIDTH
            self.y = HEIGHT //2
        self.angle = self.get_angle_from_direction(direction)
        self.rotated_image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated_image.get_rect(center=(self.x, self.y))
        self.spawn_time = pygame.time.get_ticks()


    def get_angle_from_direction(self, direction):
        if direction == 'up':
            return -90
        elif direction == 'right':
            return 180
        elif direction == 'down':
            return 90
        elif direction == 'left':
            return 0

    def update(self, player, speed_multiplier=1.0):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = (dx**2 + dy**2) ** 0.5
        self.x += (dx / dist) * self.speed * speed_multiplier
        self.y += (dy / dist) * self.speed * speed_multiplier
        self.rect.center = (self.x, self.y)

    def draw(self, screen):
        screen.blit(self.rotated_image, self.rect)

class Game:
    def __init__(self):
        self.player = Player()
        self.name = ""
        self.score = 0
        self.enemies = []
        self.death_marks = []
        self.game_paused = False
        self.leaderboard_file = 'leaderboard.csv'
        self.current_screen = 'leaderboard'
        self.beat_timestamps = []
        self.music_started = False
        self.enemy_spawn_index = 0
        self.music_file = ""
        self.music_list = []
        self.defense_direction = None
        self.block_counts = {'total': 0, 'just_in_time': 0, 'normal': 0, 'too_early': 0}
        self.blocks_per_direction = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.start_time = None
        self.end_time = None
        self.reaction_times = []

        self.speed_multiplier = 1.0
        self.background_image = None
        self.bg_position = (0, 0)
        self.player_image = None
        self.enemy_image = None
        self.explosion_frames = []
        self.load_sprites()

    def load_sprites(self):
        # Load the player's image
        self.player_image = pygame.image.load('sprites/player.png').convert_alpha()
        # Resize the player image if necessary
        self.player_image = pygame.transform.scale(self.player_image, (30, 40))  # Adjust size as needed
        self.player.image = self.player_image

        # Load the enemy's image
        self.enemy_image = pygame.image.load('sprites/enemy.png').convert_alpha()
        # Resize the enemy image if necessary
        self.enemy_image = pygame.transform.scale(self.enemy_image, (60, 60))  # Adjust size as needed

        # Chargement des frames d'explosion individuelles
        self.explosion_frames = self.load_explosion_frames()


    def load_explosion_frames(self):
        frames = []
        # Obtenir la liste des fichiers d'explosion dans le dossier 'sprites'
        explosion_files = [f for f in os.listdir('sprites') if f.endswith('.png') and '-explosion' in f]
        # Trier les fichiers par ordre numérique
        explosion_files.sort()
        for filename in explosion_files:
            frame = pygame.image.load(os.path.join('sprites', filename)).convert_alpha()
            # Redimensionner la frame si nécessaire
            frame = pygame.transform.scale(frame, (60, 60))  # Ajuster la taille selon les besoins
            frames.append(frame)
        return frames


    def load_music_list(self):
        # Load available music files
        self.music_list = [f for f in os.listdir('musics') if f.endswith('.mp3')]

    # The rest of the methods remain largely the same, but need to be adjusted to use the new sprite handling

    def select_music(self):
        # Music selection menu
        selected = 0
        while True:
            screen.fill((0, 0, 0))
            display_text("Select a music:", WIDTH // 4, 50, WHITE)
            for idx, music in enumerate(self.music_list):
                color = (0, 255, 0) if idx == selected else WHITE
                display_text(music, WIDTH // 4, 100 + idx * 40, color)
            display_text("Use UP/DOWN to navigate, ENTER to select", WIDTH // 4, HEIGHT - 50, WHITE)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(self.music_list)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(self.music_list)
                    elif event.key == pygame.K_RETURN:
                        self.music_file = os.path.join('musics', self.music_list[selected])
                        return 'name_input'
            clock.tick(30)

    def load_and_center_background(self, image_path):
        background_image = pygame.image.load(image_path).convert()
        image_width, image_height = background_image.get_size()
        scale_ratio = max(WIDTH / image_width, HEIGHT / image_height)
        new_width = int(image_width * scale_ratio)
        new_height = int(image_height * scale_ratio)
        resized_image = pygame.transform.scale(background_image, (new_width, new_height))
        x_position = (WIDTH - new_width) // 2 +20
        y_position = (HEIGHT - new_height) // 2 -30
        return resized_image, (x_position, y_position)

    def get_beat_timestamps(self):
        y, sr = librosa.load(self.music_file, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        beat_times_ms = [int(time * 1000) for time in beat_times]
        return beat_times_ms

    def save_score_csv(self):
        # Create 'players' folder if it doesn't exist
        os.makedirs('players', exist_ok=True)
        # Path to the player's CSV file
        player_file = os.path.join('players', f'{self.name}.csv')
        file_exists = os.path.isfile(player_file)
        average_reaction_time = sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0
        with open(player_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Write header if the file is new or empty
            if not file_exists or os.path.getsize(player_file) == 0:
                writer.writerow(['Name', 'Score', 'Total Blocks', 'Just in Time', 'Normal', 'Too Early',
                                 'Up', 'Down', 'Left', 'Right', 'Start Time', 'End Time', 'Duration', 'Music','Average Reaction Time'])
            duration = (self.end_time - self.start_time).total_seconds()
            writer.writerow([
                self.name,
                self.score,
                self.block_counts['total'],
                self.block_counts['just_in_time'],
                self.block_counts['normal'],
                self.block_counts['too_early'],
                self.blocks_per_direction['up'],
                self.blocks_per_direction['down'],
                self.blocks_per_direction['left'],
                self.blocks_per_direction['right'],
                self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration,
                os.path.basename(self.music_file),  # Save the music name
                average_reaction_time
            ])
        # Update the main leaderboard
        file_exists = os.path.isfile(self.leaderboard_file)
        with open(self.leaderboard_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists or os.path.getsize(self.leaderboard_file) == 0:
                writer.writerow(['Name', 'Score', 'Date','Music'])
            writer.writerow([self.name, self.score, self.end_time.strftime("%Y-%m-%d %H:%M:%S"),os.path.basename(self.music_file)])

    def load_leaderboard(self):
        leaderboard_data = []
        try:
            with open(self.leaderboard_file, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                leaderboard_data = sorted([row for row in reader], key=lambda x: int(x[1]), reverse=True)
            return leaderboard_data[:5]
        except (FileNotFoundError, StopIteration):
            return []

    def leaderboard_screen(self):
        screen.fill((0, 0, 0))
        display_text("Leaderboard", WIDTH // 2 - 80, 50, WHITE)
        leaderboard_data = self.load_leaderboard()
        y_offset = 100
        for entry in leaderboard_data:
            display_text(f"{entry[0]}: {entry[1]} - {entry[2]} - on music: {entry[3]}", WIDTH // 20, y_offset, WHITE)
            y_offset += 40
        display_text("Press ENTER to play", WIDTH // 4, HEIGHT - 100, WHITE)
        pygame.display.flip()

        # Event handling to move to music selection screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return 'select_music'
        return 'leaderboard'  # Remain on leaderboard if ENTER is not pressed

    def name_input_screen(self):
        self.name = ""
        while True:
            screen.fill((0, 0, 0))
            display_text("Enter your name: " + self.name, WIDTH // 4, HEIGHT // 3, WHITE)
            display_text("Press ENTER to start", WIDTH // 4, HEIGHT // 2, WHITE)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.name:
                        return 'game'
                    elif event.key == pygame.K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif len(self.name) < 10 and event.unicode.isalnum():
                        self.name += event.unicode
            clock.tick(30)

    def game_over_screen(self):
        screen.fill((0, 0, 0))
        display_text(f"Game Over! Score: {self.score}", WIDTH // 4, HEIGHT // 3, WHITE)
        display_text("Press ENTER to return to the main menu", WIDTH // 4, HEIGHT // 2, WHITE)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return 'leaderboard'
        return 'game_over'

    def pause_screen(self):
        pygame.mixer.music.pause()  # Pause the music
        while self.game_paused:
            screen.fill((0, 0, 0))
            display_text("Game Paused", WIDTH // 2 - 80, HEIGHT // 2 - 20, WHITE)
            display_text("Press 'P' to resume", WIDTH // 2 - 150, HEIGHT // 2 + 20, WHITE)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.game_paused = False
                    pygame.mixer.music.unpause()  # Resume the music
            clock.tick(30)

    def check_game_over(self):
        for enemy in self.enemies:
            if enemy.active:
                distance = ((self.player.x - enemy.x) ** 2 + (self.player.y - enemy.y) ** 2) ** 0.5
                if distance < self.player.size:  # If an enemy touches the player
                    return True
        return False

    def check_defense(self, player_input):
        current_time = pygame.time.get_ticks()
        for enemy in self.enemies:
            if enemy.active and enemy.direction == player_input:
                distance = ((self.player.x - enemy.x) ** 2 + (self.player.y - enemy.y) ** 2) ** 0.5
                if distance < 200:  # Maximum threshold
                    enemy.active = False
                    self.death_marks.append({'x': enemy.x, 'y': enemy.y, 'start_time': pygame.time.get_ticks()})
                    reaction_time = current_time - enemy.spawn_time  # Calcul du temps de réaction
                    self.reaction_times.append(reaction_time)  # Nouvelle liste pour stocker les temps de réaction

                    self.score += int(20 / (distance*0.02))
                    self.block_counts['total'] += 1
                    self.blocks_per_direction[player_input] += 1
                    if distance < 50:
                        self.block_counts['just_in_time'] += 1
                    elif distance < 125:
                        self.block_counts['normal'] += 1
                    else:
                        self.block_counts['too_early'] += 1

    def read_serial_input(self):
        if ser and ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                return line.lower()
        return None

    def game_loop(self):
        self.score = 0
        self.enemies.clear()
        self.death_marks.clear()
        self.defense_direction = None
        self.game_paused = False
        self.music_started = False
        self.enemy_spawn_index = 0
        self.speed_multiplier = 1.0
        self.block_counts = {'total': 0, 'just_in_time': 0, 'normal': 0, 'too_early': 0}
        self.blocks_per_direction = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.start_time = datetime.now()

        # Load background image
        self.background_image, self.bg_position = self.load_and_center_background("background.png")

        # Load beats in a separate thread
        beat_thread = threading.Thread(target=lambda: setattr(self, 'beat_timestamps', self.get_beat_timestamps()))
        beat_thread.start()
        beat_thread.join()

        # Start the music
        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.play()

        running = True
        while running:
            if not self.music_started:
                if pygame.mixer.music.get_busy():
                    self.music_started = True

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.game_paused = True
                        self.pause_screen()
                    elif event.key in (pygame.K_UP, pygame.K_z):  # Up arrow or Z
                        self.defense_direction = 'up'
                        self.check_defense(self.defense_direction)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):  # Down arrow or S
                        self.defense_direction = 'down'
                        self.check_defense(self.defense_direction)
                    elif event.key in (pygame.K_LEFT, pygame.K_q):  # Left arrow or Q
                        self.defense_direction = 'left'
                        self.check_defense(self.defense_direction)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):  # Right arrow or D
                        self.defense_direction = 'right'
                        self.check_defense(self.defense_direction)
                elif event.type == pygame.KEYUP:
                    self.defense_direction = None

            # Read serial input
            serial_input = self.read_serial_input()
            if serial_input:
                self.defense_direction = serial_input
                self.check_defense(self.defense_direction)

            # Enemy spawning based on beats
            current_time_ms = pygame.mixer.music.get_pos()
            while self.enemy_spawn_index < len(self.beat_timestamps) and current_time_ms >= self.beat_timestamps[self.enemy_spawn_index]:
                direction = random.choice(['up', 'down', 'left', 'right'])
                enemy = Enemy(direction, speed=5, image=self.enemy_image)
                self.enemies.append(enemy)
                self.enemy_spawn_index += 1

            # Check if the music has ended
            if not pygame.mixer.music.get_busy():
                # Restart the music and increase the speed
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play()
                self.speed_multiplier += 0.2  # Increase speed by 10% each loop
                self.score+=1000
                self.enemy_spawn_index = 0

            # Update enemies
            for enemy in self.enemies:
                if enemy.active:
                    enemy.update(self.player, self.speed_multiplier)

            # Check for Game Over
            if self.check_game_over():
                pygame.mixer.music.stop()
                self.end_time = datetime.now()
                self.save_score_csv()
                return 'game_over'

            # Drawing
            screen.fill((0, 0, 0))
            screen.blit(self.background_image, self.bg_position)

            # Rotate the player sprite based on defense_direction
            if self.defense_direction:
                angle = self.get_angle_from_direction(self.defense_direction)
            else:
                angle = 0  # Default angle
            rotated_player_image = pygame.transform.rotate(self.player_image, angle)
            player_rect = rotated_player_image.get_rect(center=(self.player.x, self.player.y))
            screen.blit(rotated_player_image, player_rect)

            for enemy in self.enemies:
                if enemy.active:
                    enemy.draw(screen)
            # Draw explosion animations
            current_time = pygame.time.get_ticks()
            for mark in self.death_marks[:]:
                elapsed_time = current_time - mark['start_time']
                frame_duration = 60  # Duration of each frame in ms
                frame_index = elapsed_time // frame_duration
                if frame_index < len(self.explosion_frames):
                    frame = self.explosion_frames[int(frame_index)]
                    rect = frame.get_rect(center=(mark['x'], mark['y']))
                    screen.blit(frame, rect)
                else:
                    self.death_marks.remove(mark)

            display_text(f"Score: {self.score}", 10, 10)
            pygame.display.flip()
            clock.tick(60)

    def get_angle_from_direction(self, direction):
        if direction == 'up':
            return 90
        elif direction == 'right':
            return 0
        elif direction == 'down':
            return -90
        elif direction == 'left':
            return 180

# --- Utility Functions ---

def display_text(text, x, y, color=WHITE):
    surface = FONT.render(text, True, color)
    screen.blit(surface, (x, y))

# --- Main Execution ---

def main():
    game = Game()
    game.load_music_list()
    current_screen = 'leaderboard'

    while True:
        if current_screen == 'leaderboard':
            current_screen = game.leaderboard_screen()
        elif current_screen == 'select_music':
            current_screen = game.select_music()
        elif current_screen == 'name_input':
            current_screen = game.name_input_screen()
        elif current_screen == 'game':
            current_screen = game.game_loop()
        elif current_screen == 'game_over':
            current_screen = game.game_over_screen()

if __name__ == "__main__":
    main()