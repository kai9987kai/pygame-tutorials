import json
import math
import os
import random
import sys
from pathlib import Path

import pygame


WIDTH = 960
HEIGHT = 540
FPS = 60
FLOOR_Y = HEIGHT - 58
ASSET_DIR = Path(__file__).resolve().parent
SAVE_PATH = ASSET_DIR / "save_data.json"

WHITE = (245, 248, 255)
BLACK = (10, 12, 18)
PANEL = (18, 22, 31)
YELLOW = (255, 213, 74)
CYAN = (88, 214, 255)
ORANGE = (255, 133, 64)
RED = (230, 74, 74)
GREEN = (80, 210, 126)
PURPLE = (170, 110, 255)

ENEMY_ARCHETYPES = {
    "raider": {"label": "R", "color": RED, "health": 0, "speed": 1.0, "points": 0},
    "runner": {"label": "F", "color": CYAN, "health": -1, "speed": 1.42, "points": 2},
    "brute": {"label": "B", "color": ORANGE, "health": 3, "speed": 0.72, "points": 5},
    "warden": {"label": "W", "color": PURPLE, "health": 1, "speed": 0.92, "points": 3},
}


def clamp(value, low, high):
    return max(low, min(high, value))


def asset_path(name):
    return str(ASSET_DIR / name)


def load_frames(prefix, count, suffix=""):
    frames = []
    for index in range(1, count + 1):
        image = pygame.image.load(asset_path(f"{prefix}{index}{suffix}.png")).convert_alpha()
        frames.append(image)
    return frames


def load_save():
    if not SAVE_PATH.exists():
        return {"high_score": 0}
    try:
        with SAVE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"high_score": 0}
    return {"high_score": int(data.get("high_score", 0))}


def save_high_score(score):
    data = load_save()
    if score <= data["high_score"]:
        return
    try:
        with SAVE_PATH.open("w", encoding="utf-8") as file:
            json.dump({"high_score": score}, file, indent=2)
    except OSError:
        pass


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.ready = pygame.mixer.get_init() is not None
        self.sounds = {}
        if not self.ready:
            return

        for name, filename in (("shoot", "bullet.mp3"), ("hit", "hit.mp3")):
            try:
                self.sounds[name] = pygame.mixer.Sound(asset_path(filename))
                self.sounds[name].set_volume(0.35)
            except pygame.error:
                self.sounds[name] = None

        try:
            pygame.mixer.music.load(asset_path("music.mp3"))
            pygame.mixer.music.set_volume(0.22)
            pygame.mixer.music.play(-1)
        except pygame.error:
            self.ready = False

    def play(self, name):
        sound = self.sounds.get(name)
        if self.enabled and sound:
            sound.play()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.ready:
            return self.enabled
        if self.enabled:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        return self.enabled


class Player(pygame.sprite.Sprite):
    def __init__(self, assets):
        super().__init__()
        self.assets = assets
        self.image = assets["standing"]
        self.rect = self.image.get_rect(midbottom=(180, FLOOR_Y))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.speed = 320
        self.gravity = 1680
        self.jump_velocity = -650
        self.velocity_y = 0
        self.facing = 1
        self.walk_timer = 0
        self.on_ground = True
        self.invulnerable = 0
        self.cooldown = 0
        self.shield = 0
        self.rapid = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = 1
        self.dash_speed = 820
        self.max_lives = 3
        self.lives = self.max_lives

    @property
    def collision_rect(self):
        return self.rect.inflate(-30, -12).move(0, 6)

    def reset_position(self):
        self.rect = self.image.get_rect(midbottom=(180, FLOOR_Y))
        self.pos.update(self.rect.topleft)
        self.velocity_y = 0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_velocity
            self.on_ground = False

    def start_dash(self, direction=None):
        if self.dash_cooldown > 0:
            return False
        self.dash_direction = direction or self.facing
        self.facing = self.dash_direction
        self.dash_timer = 0.16
        self.dash_cooldown = 0.95
        self.invulnerable = max(self.invulnerable, 0.2)
        self.velocity_y *= 0.25
        return True

    def update(self, keys, dt):
        moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        move = int(moving_right) - int(moving_left)
        animation_move = 0

        if self.dash_timer > 0:
            self.pos.x += self.dash_direction * self.dash_speed * dt
            self.dash_timer = max(0, self.dash_timer - dt)
            self.walk_timer += dt * 24
            animation_move = self.dash_direction
        elif move:
            self.facing = move
            self.pos.x += move * self.speed * dt
            self.walk_timer += dt * 16
            animation_move = move
        else:
            self.walk_timer = 0

        self.pos.x = clamp(self.pos.x, 8, WIDTH - self.rect.width - 8)
        self.velocity_y += self.gravity * dt
        self.pos.y += self.velocity_y * dt

        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        if self.rect.bottom >= FLOOR_Y:
            self.rect.bottom = FLOOR_Y
            self.pos.y = self.rect.y
            self.velocity_y = 0
            self.on_ground = True

        self.cooldown = max(0, self.cooldown - dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        self.shield = max(0, self.shield - dt)
        self.rapid = max(0, self.rapid - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.choose_frame(animation_move)

    def choose_frame(self, move):
        old_midbottom = self.rect.midbottom
        if move:
            frames = self.assets["walk_right"] if self.facing > 0 else self.assets["walk_left"]
            self.image = frames[int(self.walk_timer) % len(frames)]
        else:
            self.image = self.assets["walk_right"][0] if self.facing > 0 else self.assets["walk_left"][0]
        self.rect = self.image.get_rect(midbottom=old_midbottom)
        self.pos.update(self.rect.topleft)

    def draw(self, surface, offset=(0, 0)):
        if self.invulnerable and int(self.invulnerable * 12) % 2 == 0:
            return
        surface.blit(self.image, self.rect.move(offset))
        if self.shield:
            center = (self.rect.centerx + offset[0], self.rect.centery + offset[1])
            pygame.draw.circle(surface, CYAN, center, 42, 2)
            pygame.draw.circle(surface, WHITE, center, 45, 1)
        if self.dash_timer:
            start = (self.rect.centerx - self.facing * 48 + offset[0], self.rect.centery + 18 + offset[1])
            end = (self.rect.centerx - self.facing * 12 + offset[0], self.rect.centery + 18 + offset[1])
            pygame.draw.line(surface, CYAN, start, end, 4)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.radius = 6
        self.image = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (9, 9), self.radius)
        pygame.draw.circle(self.image, BLACK, (9, 9), self.radius, 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(direction * 680, 0)

    def update(self, dt):
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.image, self.rect.move(offset))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, assets, x, path_start, path_end, health, speed, wave, kind="raider"):
        super().__init__()
        self.assets = assets
        self.frames_right = assets["enemy_right"]
        self.frames_left = assets["enemy_left"]
        self.kind = kind
        self.profile = ENEMY_ARCHETYPES[kind]
        self.max_health = max(1, health + self.profile["health"])
        self.health = self.max_health
        self.speed = speed * self.profile["speed"]
        self.points = 4 + wave + self.profile["points"]
        self.path_start = path_start
        self.path_end = path_end
        self.direction = random.choice((-1, 1))
        self.frame_timer = random.random() * 10
        self.image = self.frames_right[0]
        self.rect = self.image.get_rect(midbottom=(x, FLOOR_Y))
        self.pos = pygame.Vector2(self.rect.topleft)

    @property
    def collision_rect(self):
        return self.rect.inflate(-26, -8).move(0, 4)

    def update(self, dt, speed_scale=1.0):
        self.pos.x += self.direction * self.speed * speed_scale * dt
        if self.pos.x < self.path_start:
            self.pos.x = self.path_start
            self.direction = 1
        elif self.pos.x > self.path_end:
            self.pos.x = self.path_end
            self.direction = -1

        self.frame_timer += dt * 15
        old_midbottom = self.rect.midbottom
        frames = self.frames_right if self.direction > 0 else self.frames_left
        self.image = frames[int(self.frame_timer) % len(frames)]
        self.rect = self.image.get_rect(midbottom=old_midbottom)
        self.rect.x = round(self.pos.x)
        self.rect.bottom = FLOOR_Y
        self.pos.update(self.rect.topleft)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    def draw(self, surface, font, high_contrast=False, offset=(0, 0)):
        surface.blit(self.image, self.rect.move(offset))
        bar = pygame.Rect(0, 0, 54, 8)
        bar.midbottom = (self.rect.centerx + offset[0], self.rect.top + offset[1] - 8)
        pygame.draw.rect(surface, BLACK, bar)
        fill = bar.copy()
        fill.width = round(bar.width * clamp(self.health / self.max_health, 0, 1))
        pygame.draw.rect(surface, self.profile["color"] if not high_contrast else YELLOW, fill)
        pygame.draw.rect(surface, WHITE, bar, 1)
        badge_center = (bar.left - 12, bar.centery)
        pygame.draw.circle(surface, BLACK, badge_center, 10)
        pygame.draw.circle(surface, self.profile["color"], badge_center, 8)
        label = font.render(self.profile["label"], True, BLACK)
        surface.blit(label, label.get_rect(center=badge_center))
        if high_contrast:
            health_label = font.render(str(self.health), True, BLACK)
            label_rect = health_label.get_rect(center=bar.center)
            surface.blit(health_label, label_rect)


class Pickup(pygame.sprite.Sprite):
    STYLES = {
        "shield": (CYAN, "S"),
        "rapid": (PURPLE, "R"),
        "heal": (GREEN, "+"),
    }

    def __init__(self, kind, x, font):
        super().__init__()
        self.kind = kind
        color, label = self.STYLES[kind]
        self.image = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLACK, (17, 17), 16)
        pygame.draw.circle(self.image, color, (17, 17), 14)
        pygame.draw.circle(self.image, WHITE, (17, 17), 14, 2)
        text = font.render(label, True, BLACK)
        self.image.blit(text, text.get_rect(center=(17, 16)))
        self.rect = self.image.get_rect(midbottom=(x, FLOOR_Y - 6))
        self.base_y = self.rect.y
        self.float_timer = random.random() * 6

    def update(self, dt):
        self.float_timer += dt * 5
        self.rect.y = self.base_y + round(math.sin(self.float_timer) * 4)

    def draw(self, surface, high_contrast=False, offset=(0, 0)):
        surface.blit(self.image, self.rect.move(offset))
        if high_contrast:
            pygame.draw.rect(surface, WHITE, self.rect.move(offset).inflate(6, 6), 1)


class Particle:
    def __init__(self, pos, color):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(random.uniform(-140, 140), random.uniform(-180, -40))
        self.color = color
        self.radius = random.randint(3, 7)
        self.life = random.uniform(0.25, 0.55)

    def update(self, dt):
        self.life -= dt
        self.velocity.y += 520 * dt
        self.pos += self.velocity * dt
        self.radius = max(1, self.radius - 7 * dt)
        return self.life > 0

    def draw(self, surface, offset=(0, 0)):
        alpha = clamp(self.life / 0.55, 0, 1)
        color = tuple(round(channel * alpha) for channel in self.color)
        pygame.draw.circle(surface, color, (round(self.pos.x + offset[0]), round(self.pos.y + offset[1])), round(self.radius))


class FloatingText:
    def __init__(self, text, pos, color):
        self.text = text
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.life = 1.0

    def update(self, dt):
        self.life -= dt
        self.pos.y -= 42 * dt
        return self.life > 0

    def draw(self, surface, font, offset=(0, 0)):
        alpha = clamp(self.life, 0, 1)
        color = tuple(round(channel * alpha) for channel in self.color)
        image = font.render(self.text, True, color)
        surface.blit(image, image.get_rect(center=(self.pos.x + offset[0], self.pos.y + offset[1])))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("First Game: Research Upgrade")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24, True)
        self.small_font = pygame.font.SysFont("arial", 18, True)
        self.large_font = pygame.font.SysFont("arial", 52, True)
        self.title_font = pygame.font.SysFont("arial", 64, True)
        self.assets = self.load_assets()
        self.audio = AudioManager()
        self.best_score = load_save()["high_score"]
        self.high_contrast = False
        self.assist_mode = False
        self.state = "start"
        self.running = True
        self.reset()

    def load_assets(self):
        background = pygame.image.load(asset_path("bg.jpg")).convert()
        background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))
        return {
            "background": background,
            "standing": pygame.image.load(asset_path("standing.png")).convert_alpha(),
            "walk_right": load_frames("R", 9),
            "walk_left": load_frames("L", 9),
            "enemy_right": load_frames("R", 11, "E"),
            "enemy_left": load_frames("L", 11, "E"),
        }

    def reset(self):
        self.player = Player(self.assets)
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.effects = []
        self.floaters = []
        self.score = 0
        self.wave = 0
        self.challenge_tier = 0
        self.streak = 0
        self.combo_timer = 0
        self.damage_taken = 0
        self.wave_damage = 0
        self.no_hit_time = 0
        self.shots_fired = 0
        self.hits_landed = 0
        self.completed_objectives = 0
        self.objective = None
        self.pickup_timer = 6.0
        self.next_wave_timer = 0
        self.message = "Press Enter to start"
        self.shake = 0
        self.spawn_wave()

    def spawn_wave(self):
        self.wave += 1
        accuracy = self.hits_landed / max(1, self.shots_fired)
        accuracy_pressure = (accuracy - 0.5) * 2 if self.shots_fired >= 8 else 0
        assist_offset = 1.35 if self.assist_mode else 0
        challenge = clamp(
            self.score / 28
            + self.streak / 8
            + self.no_hit_time / 34
            + accuracy_pressure
            + self.completed_objectives * 0.35
            - self.damage_taken * 0.9
            - assist_offset,
            0,
            9,
        )
        self.challenge_tier = challenge
        self.wave_damage = 0
        enemy_count = min(2 + self.wave // 2 + int(challenge // 2), 8)
        health = 2 + self.wave // 2 + int(challenge // 3)
        speed = 82 + self.wave * 9 + challenge * 9
        spacing = (WIDTH - 360) / max(enemy_count, 1)

        for index in range(enemy_count):
            path_start = 360 + index * spacing
            path_end = min(WIDTH - 90, path_start + random.randint(130, 240))
            x = random.randint(round(path_start), round(path_end))
            kind = self.choose_enemy_kind(challenge)
            self.enemies.add(Enemy(self.assets, x, path_start, path_end, health, speed, self.wave, kind))

        self.message = f"Wave {self.wave}: clear {enemy_count} threats"
        self.choose_objective()
        self.add_floater(f"Wave {self.wave}", (WIDTH // 2, 116), YELLOW)

    def choose_enemy_kind(self, challenge):
        choices = [("raider", 7)]
        if self.wave >= 2:
            choices.append(("runner", 2 + int(challenge)))
        if self.wave >= 3:
            choices.append(("brute", 2 + self.wave // 2))
        if self.wave >= 4:
            choices.append(("warden", 1 + int(challenge // 2)))
        kinds, weights = zip(*choices)
        return random.choices(kinds, weights=weights, k=1)[0]

    def choose_objective(self):
        options = [
            ("streak", min(4 + self.wave, 12), f"Land a {min(4 + self.wave, 12)} hit combo"),
            ("dash", min(2 + self.wave // 2, 6), f"Dash {min(2 + self.wave // 2, 6)} times"),
            ("pickup", 1, "Collect a pickup"),
        ]
        if self.wave >= 2:
            options.append(("no_damage", 1, "Clear wave without damage"))
        kind, target, label = random.choice(options)
        self.objective = {"kind": kind, "target": target, "progress": 0, "label": label, "rewarded": False}

    def spawn_pickup(self):
        kind = random.choices(("shield", "rapid", "heal"), weights=(4, 4, 2), k=1)[0]
        x = random.randint(260, WIDTH - 90)
        self.pickups.add(Pickup(kind, x, self.small_font))

    def add_particles(self, pos, color, count=8):
        for _ in range(count):
            self.effects.append(Particle(pos, color))

    def add_floater(self, text, pos, color=WHITE):
        self.floaters.append(FloatingText(text, pos, color))

    def objective_text(self):
        if not self.objective:
            return ""
        if self.objective["kind"] == "no_damage" and self.wave_damage:
            return f"Objective failed: {self.objective['label']}"
        progress = min(self.objective["progress"], self.objective["target"])
        return f"Objective: {self.objective['label']} ({progress}/{self.objective['target']})"

    def advance_objective(self, kind, amount=1, absolute=False):
        if not self.objective or self.objective["kind"] != kind or self.objective["rewarded"]:
            return
        if absolute:
            self.objective["progress"] = max(self.objective["progress"], amount)
        else:
            self.objective["progress"] += amount
        if self.objective["progress"] >= self.objective["target"]:
            self.complete_objective()

    def complete_objective(self):
        if not self.objective or self.objective["rewarded"]:
            return
        self.objective["rewarded"] = True
        self.completed_objectives += 1
        reward = 8 + self.wave * 2
        self.score += reward
        self.add_floater(f"Objective +{reward}", (WIDTH // 2, 102), GREEN)
        if len(self.pickups) < 3:
            self.spawn_pickup()

    def trigger_dash(self):
        keys = pygame.key.get_pressed()
        direction = self.player.facing
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction = 1
        if self.player.start_dash(direction):
            self.add_particles(self.player.rect.center, CYAN, 10)
            self.add_floater("Dash", self.player.rect.midtop, CYAN)
            self.advance_objective("dash")

    def attempt_shoot(self):
        limit = 8 if self.player.rapid else 5
        if self.player.cooldown > 0 or len(self.bullets) >= limit:
            return
        x = self.player.rect.centerx + self.player.facing * 30
        y = self.player.rect.centery - 6
        self.bullets.add(Bullet(x, y, self.player.facing))
        self.player.cooldown = 0.13 if self.player.rapid else 0.32
        self.shots_fired += 1
        self.audio.play("shoot")
        self.add_particles((x, y), YELLOW, 4)

    def apply_pickup(self, pickup):
        if pickup.kind == "shield":
            self.player.shield = max(self.player.shield, 8.0)
            label = "Shield"
            color = CYAN
        elif pickup.kind == "rapid":
            self.player.rapid = max(self.player.rapid, 7.0)
            label = "Rapid"
            color = PURPLE
        else:
            if self.player.lives < self.player.max_lives:
                self.player.lives += 1
                label = "+1 life"
            else:
                self.score += 5
                label = "+5 score"
            color = GREEN
        self.add_particles(pickup.rect.center, color, 12)
        self.add_floater(label, pickup.rect.midtop, color)
        self.advance_objective("pickup")

    def handle_player_hit(self, enemy):
        if self.player.invulnerable:
            return
        self.audio.play("hit")
        if self.player.shield:
            self.player.shield = 0
            enemy.take_damage(enemy.health)
            self.score += 3
            self.add_particles(enemy.rect.center, CYAN, 18)
            self.add_floater("Shield block", self.player.rect.midtop, CYAN)
            self.shake = 0.18
            return

        self.player.lives -= 1
        self.damage_taken += 1
        self.wave_damage += 1
        self.streak = 0
        self.combo_timer = 0
        self.no_hit_time = 0
        self.player.invulnerable = 2.0 if self.assist_mode else 1.4
        self.player.reset_position()
        self.add_particles(enemy.rect.center, RED, 18)
        self.add_floater("-1 life", (self.player.rect.centerx, self.player.rect.top - 14), RED)
        self.shake = 0.28
        if self.player.lives <= 0:
            self.state = "game_over"
            save_high_score(self.score)
            self.best_score = max(self.best_score, self.score)

    def update_playing(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.jump()
        if keys[pygame.K_SPACE]:
            self.attempt_shoot()

        self.player.update(keys, dt)
        self.bullets.update(dt)
        speed_scale = 0.82 if self.assist_mode else 1.0
        self.enemies.update(dt, speed_scale)
        self.pickups.update(dt)
        self.no_hit_time += dt
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer <= 0:
            self.streak = 0
        self.pickup_timer -= dt
        self.shake = max(0, self.shake - dt)

        if self.pickup_timer <= 0:
            self.spawn_pickup()
            self.pickup_timer = random.uniform(8.0, 13.0)

        for bullet, enemies in pygame.sprite.groupcollide(self.bullets, self.enemies, True, False).items():
            for enemy in enemies:
                killed = enemy.take_damage(1)
                self.audio.play("hit")
                self.streak += 1
                self.combo_timer = 2.35
                self.hits_landed += 1
                combo_bonus = min(4, self.streak // 5)
                self.score += 1 + combo_bonus
                self.add_particles(bullet.rect.center, ORANGE, 8)
                self.add_floater(f"+{1 + combo_bonus}", bullet.rect.center, YELLOW)
                self.advance_objective("streak", self.streak, absolute=True)
                if killed:
                    self.score += enemy.points
                    self.add_particles(enemy.rect.center, enemy.profile["color"], 18)
                    self.add_floater(f"+{enemy.points}", enemy.rect.midtop, GREEN)
                    if random.random() < 0.16:
                        self.pickups.add(Pickup(random.choice(("shield", "rapid", "heal")), enemy.rect.centerx, self.small_font))

        for pickup in pygame.sprite.spritecollide(self.player, self.pickups, True):
            self.apply_pickup(pickup)

        for enemy in list(self.enemies):
            if self.player.collision_rect.colliderect(enemy.collision_rect):
                self.handle_player_hit(enemy)
                break

        self.effects = [particle for particle in self.effects if particle.update(dt)]
        self.floaters = [floater for floater in self.floaters if floater.update(dt)]

        if not self.enemies:
            if self.next_wave_timer <= 0:
                if self.objective and self.objective["kind"] == "no_damage" and self.wave_damage == 0:
                    self.advance_objective("no_damage")
                self.next_wave_timer = 2.0
                self.message = "Wave cleared"
                self.add_floater("Wave cleared", (WIDTH // 2, 125), GREEN)
            else:
                self.next_wave_timer -= dt
                if self.next_wave_timer <= 0:
                    self.spawn_wave()

    def handle_keydown(self, event):
        if event.key == pygame.K_m:
            enabled = self.audio.toggle()
            self.add_floater("Audio on" if enabled else "Audio off", (WIDTH - 100, 76), CYAN)
        elif event.key == pygame.K_c:
            self.high_contrast = not self.high_contrast
            self.add_floater("High contrast" if self.high_contrast else "Standard contrast", (WIDTH - 130, 104), YELLOW)
        elif event.key == pygame.K_f:
            self.assist_mode = not self.assist_mode
            self.add_floater("Assist on" if self.assist_mode else "Assist off", (WIDTH - 116, 132), GREEN)

        if self.state == "start":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "playing"
                self.message = "Clear the wave"
        elif self.state == "playing":
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.player.jump()
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_x):
                self.trigger_dash()
        elif self.state == "paused":
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "playing"
        elif self.state == "game_over":
            if event.key == pygame.K_r:
                self.reset()
                self.state = "playing"
            elif event.key == pygame.K_ESCAPE:
                self.running = False

    def draw(self):
        offset = (0, 0)
        if self.shake:
            power = int(10 * self.shake / 0.28)
            offset = (random.randint(-power, power), random.randint(-power, power))

        self.screen.fill(BLACK)
        self.screen.blit(self.assets["background"], offset)
        pygame.draw.rect(self.screen, (34, 42, 34), (0, FLOOR_Y + offset[1], WIDTH, HEIGHT - FLOOR_Y))
        pygame.draw.line(self.screen, WHITE if self.high_contrast else (80, 94, 84), (0, FLOOR_Y), (WIDTH, FLOOR_Y), 2)

        for pickup in self.pickups:
            pickup.draw(self.screen, self.high_contrast, offset)
        for bullet in self.bullets:
            bullet.draw(self.screen, offset)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.small_font, self.high_contrast, offset)
        self.player.draw(self.screen, offset)
        for particle in self.effects:
            particle.draw(self.screen, offset)
        for floater in self.floaters:
            floater.draw(self.screen, self.small_font, offset)

        self.draw_hud()
        if self.state == "start":
            self.draw_start()
        elif self.state == "paused":
            self.draw_pause()
        elif self.state == "game_over":
            self.draw_game_over()

        pygame.display.flip()

    def draw_hud(self):
        panel = pygame.Surface((WIDTH, 104), pygame.SRCALPHA)
        panel.fill((PANEL[0], PANEL[1], PANEL[2], 205 if not self.high_contrast else 235))
        self.screen.blit(panel, (0, 0))
        self.draw_text(f"Score {self.score}", 24, 14, self.font, YELLOW)
        self.draw_text(f"Best {self.best_score}", 154, 14, self.small_font, WHITE)
        self.draw_text(f"Wave {self.wave}", 284, 14, self.small_font, WHITE)
        self.draw_text(f"Lives {self.player.lives}", 384, 14, self.small_font, RED if self.player.lives == 1 else WHITE)
        self.draw_text(self.message, 24, 46, self.small_font, WHITE)
        self.draw_text(self.objective_text(), 24, 74, self.small_font, GREEN if self.objective and self.objective["rewarded"] else WHITE)
        self.draw_text(f"Enemies {len(self.enemies)}", 284, 46, self.small_font, WHITE)
        self.draw_text(f"Challenge {self.challenge_tier:0.1f}", 384, 46, self.small_font, YELLOW)

        cooldown_width = 90
        cooldown = 1 - clamp(self.player.cooldown / (0.13 if self.player.rapid else 0.32), 0, 1)
        cooldown_rect = pygame.Rect(486, 22, cooldown_width, 10)
        pygame.draw.rect(self.screen, BLACK, cooldown_rect)
        filled = cooldown_rect.copy()
        filled.width = round(cooldown_width * cooldown)
        pygame.draw.rect(self.screen, YELLOW, filled)
        pygame.draw.rect(self.screen, WHITE, cooldown_rect, 1)
        self.draw_text("Shot", 486, 38, self.small_font, WHITE)

        dash_ready = 1 - clamp(self.player.dash_cooldown / 0.95, 0, 1)
        dash_rect = pygame.Rect(486, 62, cooldown_width, 10)
        pygame.draw.rect(self.screen, BLACK, dash_rect)
        dash_fill = dash_rect.copy()
        dash_fill.width = round(cooldown_width * dash_ready)
        pygame.draw.rect(self.screen, CYAN, dash_fill)
        pygame.draw.rect(self.screen, WHITE, dash_rect, 1)
        self.draw_text("Dash", 486, 78, self.small_font, WHITE)

        x = 610
        if self.player.shield:
            self.draw_text(f"Shield {self.player.shield:0.1f}", x, 18, self.small_font, CYAN)
            x += 130
        if self.player.rapid:
            self.draw_text(f"Rapid {self.player.rapid:0.1f}", x, 18, self.small_font, PURPLE)
            x += 120
        if self.streak:
            combo_bonus = min(4, self.streak // 5)
            self.draw_text(f"Combo {self.streak} +{combo_bonus}", 610, 54, self.small_font, YELLOW)

        audio = "Audio on" if self.audio.enabled else "Audio off"
        contrast = "Contrast on" if self.high_contrast else "Contrast off"
        assist = "Assist on" if self.assist_mode else "Assist off"
        self.draw_text(audio, WIDTH - 178, 10, self.small_font, CYAN)
        self.draw_text(contrast, WIDTH - 178, 34, self.small_font, YELLOW if self.high_contrast else WHITE)
        self.draw_text(assist, WIDTH - 178, 58, self.small_font, GREEN if self.assist_mode else WHITE)

    def draw_start(self):
        self.draw_overlay()
        self.draw_text("FIRST GAME", WIDTH // 2, 150, self.title_font, YELLOW, center=True)
        self.draw_text("Research upgrade", WIDTH // 2, 212, self.font, WHITE, center=True)
        self.draw_text("Enter / Space: start", WIDTH // 2, 282, self.font, WHITE, center=True)
        self.draw_text("Move: arrows or WASD   Shoot: Space   Dash: Shift or X   Pause: P", WIDTH // 2, 324, self.small_font, WHITE, center=True)
        self.draw_text("M: audio   C: contrast   F: assist   R: restart after game over", WIDTH // 2, 352, self.small_font, WHITE, center=True)

    def draw_pause(self):
        self.draw_overlay()
        self.draw_text("Paused", WIDTH // 2, 220, self.large_font, YELLOW, center=True)
        self.draw_text("Press P or Escape to resume", WIDTH // 2, 286, self.font, WHITE, center=True)

    def draw_game_over(self):
        self.draw_overlay()
        self.draw_text("Game over", WIDTH // 2, 188, self.large_font, RED, center=True)
        self.draw_text(f"Score {self.score}   Best {self.best_score}", WIDTH // 2, 256, self.font, WHITE, center=True)
        self.draw_text("Press R to retry or Escape to quit", WIDTH // 2, 316, self.font, WHITE, center=True)

    def draw_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150 if not self.high_contrast else 205))
        self.screen.blit(overlay, (0, 0))

    def draw_text(self, text, x, y, font, color, center=False):
        image = font.render(text, True, color)
        rect = image.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        if self.high_contrast:
            outline = font.render(text, True, BLACK)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                outline_rect = rect.move(dx, dy)
                self.screen.blit(outline, outline_rect)
        self.screen.blit(image, rect)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            dt = min(dt, 1 / 30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)

            if self.state == "playing":
                self.update_playing(dt)
            else:
                self.effects = [particle for particle in self.effects if particle.update(dt)]
                self.floaters = [floater for floater in self.floaters if floater.update(dt)]
            self.draw()

        pygame.quit()


def main():
    if "--self-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        game = Game()
        game.state = "playing"
        for _ in range(12):
            game.update_playing(1 / FPS)
            game.draw()
        pygame.quit()
        return
    Game().run()


if __name__ == "__main__":
    main()
