import pygame
import random
import sys
import math
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# --- Constants ---
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 700
FPS = 60

# Layers (Z-Index)
LAYER_BG = 0
LAYER_STAR = 1
LAYER_PARTICLE = 2
LAYER_POWERUP = 3
LAYER_ENEMY = 4
LAYER_PLAYER = 5
LAYER_BULLET = 6
LAYER_UI = 7

# Enhanced Neon Color Palette
COLOR_BG = (8, 8, 18)
COLOR_PLAYER = (0, 255, 255)
COLOR_BULLET = (255, 50, 80)
COLOR_ENEMY = (255, 0, 255)
COLOR_PARTICLE = (255, 255, 200)
COLOR_POWERUP_SHIELD = (100, 200, 255)
COLOR_POWERUP_RAPID = (255, 200, 0)
COLOR_POWERUP_SPREAD = (0, 255, 150)
COLOR_COMBO_TEXT = (255, 255, 100)

# Game Physics
PLAYER_MAX_SPEED = 750
PLAYER_ACCEL = 5000
PLAYER_FRICTION = 12
BULLET_SPEED = 900
ENEMY_MIN_SPEED = 120
ENEMY_MAX_SPEED = 320

class PowerUpType(Enum):
    SHIELD = 1
    RAPID_FIRE = 2
    SPREAD_SHOT = 3

@dataclass
class PowerUpConfig:
    color: Tuple[int, int, int]
    duration: float
    symbol: str

POWERUP_CONFIGS = {
    PowerUpType.SHIELD: PowerUpConfig((100, 200, 255), 8.0, "◆"),
    PowerUpType.RAPID_FIRE: PowerUpConfig((255, 200, 0), 6.0, "⚡"),
    PowerUpType.SPREAD_SHOT: PowerUpConfig((0, 255, 150), 7.0, "⊕"),
}

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, layer):
        super().__init__(groups)
        self._layer = layer
        self.size = random.randint(1, 4)
        
        # Enhanced star rendering with glow effect
        glow_size = self.size + 2
        self.image = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        shade = random.randint(80, 200)
        color = (shade, shade, shade + 50)
        
        # Draw glow
        for i in range(glow_size, 0, -1):
            alpha = int(255 * (1 - i / glow_size) * 0.3)
            glow_color = (*color, alpha)
            pygame.draw.circle(self.image, glow_color, (glow_size//2, glow_size//2), i//2)
        
        # Draw core
        pygame.draw.circle(self.image, color, (glow_size//2, glow_size//2), max(1, self.size//2))
        
        self.rect = self.image.get_rect(
            center=(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        )
        self.speed = self.size * 25
        self.twinkle_timer = random.uniform(0, 2)
        self.twinkle_speed = random.uniform(0.5, 2)

    def update(self, dt):
        self.rect.y += self.speed * dt
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
            self.rect.x = random.randint(0, SCREEN_WIDTH)
        
        # Twinkle effect
        self.twinkle_timer += dt * self.twinkle_speed
        alpha = int(150 + 105 * math.sin(self.twinkle_timer))
        self.image.set_alpha(alpha)

class Particle(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, color, size_range=(2,6), speed_range=(50, 250), 
                 life_range=(0.3, 1.2), gravity=0):
        super().__init__(groups)
        self._layer = LAYER_PARTICLE
        
        size = random.randint(*size_range)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Glow effect for particles
        for i in range(size, 0, -1):
            alpha = int(255 * (1 - i / size))
            glow_color = (*color[:3], alpha)
            pygame.draw.circle(self.image, glow_color, (size//2, size//2), i//2)
        
        self.rect = self.image.get_rect(center=(x, y))
        
        angle = random.uniform(0, 360)
        speed = random.uniform(*speed_range)
        self.velocity = pygame.math.Vector2(speed, 0).rotate(angle)
        
        self.life = random.uniform(*life_range)
        self.initial_life = self.life
        self.color = color
        self.gravity = gravity

    def update(self, dt):
        self.velocity.y += self.gravity * dt
        self.rect.centerx += self.velocity.x * dt
        self.rect.centery += self.velocity.y * dt
        self.life -= dt
        
        if self.life <= 0:
            self.kill()
            return
        
        # Smooth alpha fade
        try:
            alpha = int((self.life / self.initial_life) * 255)
            alpha = max(0, min(255, alpha))  # Clamp to valid range
            self.image.set_alpha(alpha)
        except:
            pass

class TrailParticle(pygame.sprite.Sprite):
    """Small trailing particles for bullets and enemies"""
    def __init__(self, groups, x, y, color, size=3):
        super().__init__(groups)
        self._layer = LAYER_PARTICLE
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.life = 0.15
        self.initial_life = self.life

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return
        try:
            alpha = int((self.life / self.initial_life) * 200)
            alpha = max(0, min(255, alpha))
            self.image.set_alpha(alpha)
        except:
            pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, all_sprites, bullets_group, x, y, angle=0, speed=BULLET_SPEED):
        super().__init__(all_sprites, bullets_group)
        self._layer = LAYER_BULLET
        
        # Enhanced bullet with glow
        self.image = pygame.Surface((8, 18), pygame.SRCALPHA)
        
        # Outer glow
        pygame.draw.ellipse(self.image, (*COLOR_BULLET, 100), (0, 0, 8, 18))
        # Core
        pygame.draw.ellipse(self.image, COLOR_BULLET, (1, 1, 6, 16))
        # Highlight
        pygame.draw.ellipse(self.image, (255, 150, 150), (2, 2, 4, 8))
        
        if angle != 0:
            self.image = pygame.transform.rotate(self.image, -angle)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        # Velocity for angled shots
        self.velocity = pygame.math.Vector2(0, -speed).rotate(angle)
        self.position = pygame.math.Vector2(x, y)
        
        self.trail_timer = 0
        self.all_sprites = all_sprites

    def update(self, dt):
        self.position += self.velocity * dt
        self.rect.center = round(self.position.x), round(self.position.y)
        
        # Spawn trail
        self.trail_timer += dt
        if self.trail_timer > 0.02:
            self.trail_timer = 0
            TrailParticle(self.all_sprites, self.rect.centerx, self.rect.centery, 
                         (255, 100, 100), size=4)
        
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or 
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, powerup_type: PowerUpType):
        super().__init__(groups)
        self._layer = LAYER_POWERUP
        
        self.powerup_type = powerup_type
        config = POWERUP_CONFIGS[powerup_type]
        
        # Create pulsing power-up visual
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.original_image = self.image.copy()
        
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 150)
        
        self.pulse_timer = 0
        self.rotation = 0
        self.config = config
        
        self.render_powerup(size, 1.0)

    def render_powerup(self, size, scale):
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = self.config.color
        
        # Outer glow
        for i in range(5, 0, -1):
            alpha = int(100 * (1 - i/5) * scale)
            pygame.draw.circle(self.image, (*color, alpha), (size//2, size//2), size//2 - i)
        
        # Core shape
        inner_size = int((size - 10) * scale)
        pygame.draw.circle(self.image, color, (size//2, size//2), inner_size//2)
        
        # Symbol
        font = pygame.font.Font(None, 24)
        text = font.render(self.config.symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=(size//2, size//2))
        self.image.blit(text, text_rect)

    def update(self, dt):
        self.position += self.velocity * dt
        self.rect.center = round(self.position.x), round(self.position.y)
        
        # Pulse animation
        self.pulse_timer += dt * 4
        scale = 0.9 + 0.1 * math.sin(self.pulse_timer)
        self.render_powerup(30, scale)
        
        # Rotation
        self.rotation += dt * 90
        self.image = pygame.transform.rotate(self.original_image, self.rotation)
        self.rect = self.image.get_rect(center=self.rect.center)
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, groups, speed_modifier=0, enemy_type="normal"):
        super().__init__(groups)
        self._layer = LAYER_ENEMY
        
        self.enemy_type = enemy_type
        self.create_image()
        
        self.rect = self.image.get_rect(center=(random.randint(40, SCREEN_WIDTH-40), -30))
        
        if enemy_type == "fast":
            self.speed_y = random.randint(ENEMY_MIN_SPEED + 100, int(ENEMY_MAX_SPEED + 150 + speed_modifier))
            self.hp = 1
        elif enemy_type == "tank":
            self.speed_y = random.randint(ENEMY_MIN_SPEED - 20, int(ENEMY_MAX_SPEED - 50 + speed_modifier))
            self.hp = 3
        elif enemy_type == "boss":
            self.speed_y = random.randint(ENEMY_MIN_SPEED - 40, int(ENEMY_MAX_SPEED - 100 + speed_modifier))
            self.hp = 10
        else:  # normal
            self.speed_y = random.randint(ENEMY_MIN_SPEED, int(ENEMY_MAX_SPEED + speed_modifier))
            self.hp = 2
        
        self.max_hp = self.hp
        
        # Enhanced sine wave AI
        self.t = random.uniform(0, 360)
        if enemy_type == "boss":
            self.freq = random.uniform(0.8, 1.5)
            self.amp = random.uniform(100, 200)
        else:
            self.freq = random.uniform(1.5, 4)
            self.amp = random.uniform(60, 180)
        
        self.center_x = float(self.rect.centerx)
        self.position = pygame.math.Vector2(self.rect.center)
        
        self.trail_timer = 0
        self.hit_flash = 0

    def create_image(self):
        """Create enemy sprite based on type"""
        if self.enemy_type == "boss":
            size = 80
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Boss design - menacing large enemy
            color = (200, 0, 150)
            
            # Outer spiky shell
            points = []
            for i in range(8):
                angle = i * 45
                rad = size // 2 if i % 2 == 0 else size // 3
                x = size//2 + rad * math.cos(math.radians(angle))
                y = size//2 + rad * math.sin(math.radians(angle))
                points.append((x, y))
            pygame.draw.polygon(self.image, color, points)
            
            # Inner core
            pygame.draw.circle(self.image, (255, 50, 255), (size//2, size//2), size//4)
            
            # Glowing center
            for i in range(3, 0, -1):
                alpha = int(200 * (1 - i/3))
                pygame.draw.circle(self.image, (*color, alpha), (size//2, size//2), i * 8)
            
            # Add some detail lines
            pygame.draw.circle(self.image, (255, 200, 255), (size//2, size//2), size//5, 2)
            
        elif self.enemy_type == "tank":
            # Large, tough enemy
            size = 35
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            color = (200, 0, 200)
            pygame.draw.polygon(self.image, color, 
                              [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)])
            pygame.draw.polygon(self.image, (255, 100, 255), 
                              [(size//2, 5), (size-5, size//2), (size//2, size-5), (5, size//2)])
        elif self.enemy_type == "fast":
            # Small, fast enemy
            size = 25
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            color = (255, 50, 255)
            points = []
            for i in range(6):
                angle = i * 60
                rad = size // 2 if i % 2 == 0 else size // 4
                x = size//2 + rad * math.cos(math.radians(angle))
                y = size//2 + rad * math.sin(math.radians(angle))
                points.append((x, y))
            pygame.draw.polygon(self.image, color, points)
            pygame.draw.polygon(self.image, (255, 150, 255), 
                              [(p[0] * 0.7 + size//2 * 0.3, p[1] * 0.7 + size//2 * 0.3) for p in points])
        else:
            # Normal enemy
            size = 30
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            color = COLOR_ENEMY
            pygame.draw.polygon(self.image, color, 
                              [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)])
            pygame.draw.polygon(self.image, (255, 200, 255), 
                              [(size//2, 5), (size-5, size//2), (size//2, size-5), (5, size//2)])
        
        self.original_image = self.image.copy()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.position.y += self.speed_y * dt
        self.t += dt
        
        # Sine wave movement
        offset_x = math.sin(self.t * self.freq) * self.amp
        self.rect.centerx = round(self.center_x + offset_x)
        self.rect.centery = round(self.position.y)
        
        # Hit flash effect
        if self.hit_flash > 0:
            self.hit_flash -= dt * 5
            flash_surf = self.original_image.copy()
            flash_surf.fill((255, 255, 255, int(self.hit_flash * 255)), special_flags=pygame.BLEND_RGB_ADD)
            self.image = flash_surf
        else:
            self.image = self.original_image.copy()
        
        # Trail particles
        self.trail_timer += dt
        if self.trail_timer > 0.08:
            self.trail_timer = 0
            # Will be added by game class
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw_hp_bar(self, surface):
        """Draw HP bar above boss enemies"""
        if self.enemy_type == "boss" and self.hp > 0 and hasattr(self, 'rect'):
            bar_width = 60
            bar_height = 6
            x = self.rect.centerx - bar_width // 2
            y = self.rect.top - 15
            
            # Background
            pygame.draw.rect(surface, (100, 0, 0), (x, y, bar_width, bar_height))
            
            # HP
            hp_ratio = max(0, min(1, self.hp / self.max_hp))  # Clamp between 0 and 1
            pygame.draw.rect(surface, (255, 0, 100), (x, y, int(bar_width * hp_ratio), bar_height))
            
            # Border
            pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_width, bar_height), 1)

    def take_damage(self, damage=1):
        self.hp -= damage
        self.hit_flash = 1.0
        return self.hp <= 0

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, bullets_group):
        super().__init__(groups)
        self._layer = LAYER_PLAYER
        
        # Enhanced player sprite with glow
        size = (50, 60)
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        
        # Outer glow
        for i in range(5):
            alpha = int(80 * (1 - i/5))
            glow_offset = i * 2
            points = [(25, 0-glow_offset), (50+glow_offset, 60), (25, 50), (0-glow_offset, 60)]
            pygame.draw.polygon(self.image, (*COLOR_PLAYER, alpha), points)
        
        # Main body
        pygame.draw.polygon(self.image, COLOR_PLAYER, [(25, 0), (50, 60), (25, 50), (0, 60)])
        # Highlight
        pygame.draw.polygon(self.image, (200, 255, 255), [(25, 10), (35, 50), (25, 42), (15, 50)])
        # Cockpit
        pygame.draw.circle(self.image, (100, 255, 255), (25, 25), 5)
        
        self.original_image = self.image.copy()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(self.rect.center)
        
        self.groups_ref = groups
        self.bullets_group = bullets_group
        self.last_shot = 0
        self.shoot_delay = 0.15
        
        # Health & Invulnerability
        self.max_health = 3
        self.health = self.max_health
        self.invulnerability_timer = 0
        self.invulnerability_duration = 2.0
        
        # Power-ups
        self.active_powerups = {}
        self.has_shield = False
        self.shield_alpha = 0
        
        # Engine glow
        self.engine_glow = 0

    def update(self, dt):
        self.handle_input(dt)
        self.apply_physics(dt)
        self.constrain_movement()
        self.update_powerups(dt)
        self.update_invulnerability(dt)
        self.update_visuals(dt)

    def update_invulnerability(self, dt):
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= dt

    def take_damage(self, damage=1):
        if self.has_shield:
            self.has_shield = False
            self.invulnerability_timer = 1.0 # Brief invuln after shield break
            return False
            
        if self.invulnerability_timer <= 0:
            self.health -= damage
            self.invulnerability_timer = self.invulnerability_duration
            return self.health <= 0
        return False

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        accel = pygame.math.Vector2(0, 0)
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: accel.x = -PLAYER_ACCEL
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: accel.x = PLAYER_ACCEL
        if keys[pygame.K_w] or keys[pygame.K_UP]: accel.y = -PLAYER_ACCEL
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: accel.y = PLAYER_ACCEL
        
        # Shooting
        if mouse[0] or keys[pygame.K_SPACE]:
            self.shoot()
            
        if accel.length() > 0:
            accel = accel.normalize() * PLAYER_ACCEL
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.spawn_thrusters()
                self.engine_glow = 1.0

        self.velocity += accel * dt

    def spawn_thrusters(self):
        """Enhanced thruster particles"""
        for _ in range(3):
            offset_x = random.randint(-12, 12)
            color = random.choice([(0, 255, 255), (0, 200, 255), (100, 255, 255)])
            Particle(self.groups_ref, 
                    self.rect.centerx + offset_x, 
                    self.rect.bottom - 5, 
                    color,
                    size_range=(3, 6), 
                    speed_range=(80, 150), 
                    life_range=(0.15, 0.4),
                    gravity=100)

    def shoot(self):
        now = pygame.time.get_ticks() / 1000.0
        
        # Rapid fire power-up
        shoot_delay = self.shoot_delay
        if PowerUpType.RAPID_FIRE in self.active_powerups:
            shoot_delay *= 0.4
        
        if now - self.last_shot > shoot_delay:
            self.last_shot = now
            
            # Spread shot power-up
            if PowerUpType.SPREAD_SHOT in self.active_powerups:
                angles = [-20, 0, 20]
                for angle in angles:
                    Bullet(self.groups_ref, self.bullets_group, self.rect.centerx, self.rect.top, angle=angle)
            else:
                Bullet(self.groups_ref, self.bullets_group, self.rect.centerx, self.rect.top)
            
            # Muzzle flash particles
            for _ in range(4):
                Particle(self.groups_ref, 
                        self.rect.centerx + random.randint(-5, 5), 
                        self.rect.top,
                        (255, 200, 100),
                        size_range=(2, 4),
                        speed_range=(30, 80),
                        life_range=(0.1, 0.2))

    def apply_physics(self, dt):
        self.velocity -= self.velocity * PLAYER_FRICTION * dt
        
        # Speed cap
        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)
        
        self.position += self.velocity * dt
        self.rect.center = round(self.position.x), round(self.position.y)

    def constrain_movement(self):
        if self.rect.left < 0: 
            self.rect.left = 0
            self.position.x = self.rect.centerx
            self.velocity.x = 0
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH
            self.position.x = self.rect.centerx
            self.velocity.x = 0
        if self.rect.top < 0: 
            self.rect.top = 0
            self.position.y = self.rect.centery
            self.velocity.y = 0
        if self.rect.bottom > SCREEN_HEIGHT: 
            self.rect.bottom = SCREEN_HEIGHT
            self.position.y = self.rect.centery
            self.velocity.y = 0

    def activate_powerup(self, powerup_type: PowerUpType):
        config = POWERUP_CONFIGS[powerup_type]
        self.active_powerups[powerup_type] = config.duration
        
        if powerup_type == PowerUpType.SHIELD:
            self.has_shield = True

    def update_powerups(self, dt):
        to_remove = []
        for powerup_type, time_left in self.active_powerups.items():
            time_left -= dt
            if time_left <= 0:
                to_remove.append(powerup_type)
                if powerup_type == PowerUpType.SHIELD:
                    self.has_shield = False
            else:
                self.active_powerups[powerup_type] = time_left
        
        for powerup_type in to_remove:
            del self.active_powerups[powerup_type]

    def update_visuals(self, dt):
        """Update visual effects"""
        # Engine glow decay
        if self.engine_glow > 0:
            self.engine_glow -= dt * 3
        
        # Shield visual
        if self.has_shield:
            self.shield_alpha = 100 + 50 * math.sin(pygame.time.get_ticks() / 200)
        else:
            self.shield_alpha = 0
        
        # Recreate image with effects
        self.image = self.original_image.copy()
        
        # Invulnerability Flash
        if self.invulnerability_timer > 0:
            flash_on = (int(pygame.time.get_ticks() / 100) % 2) == 0
            if flash_on:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)
        
        # Draw shield
        if self.shield_alpha > 0:
            shield_surf = pygame.Surface((70, 80), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (*COLOR_POWERUP_SHIELD, int(self.shield_alpha)), 
                             (35, 40), 35, 3)
            shield_rect = shield_surf.get_rect(center=(25, 30))
            self.image.blit(shield_surf, shield_rect.topleft)

class ComboDisplay:
    def __init__(self):
        self.combo = 0
        self.combo_timer = 0
        self.combo_timeout = 1.5
        self.display_scale = 1.0
        self.font = pygame.font.Font(None, 48)
        
    def add_kill(self):
        self.combo += 1
        self.combo_timer = self.combo_timeout
        self.display_scale = 1.5
        
    def update(self, dt):
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
        
        if self.display_scale > 1.0:
            self.display_scale -= dt * 2
            self.display_scale = max(1.0, self.display_scale)
    
    def draw(self, screen):
        if self.combo > 1:
            size = int(48 * self.display_scale)
            font = pygame.font.Font(None, size)
            
            combo_text = f"{self.combo}x COMBO!"
            text_surf = font.render(combo_text, True, COLOR_COMBO_TEXT)
            
            # Add glow
            glow_surf = font.render(combo_text, True, (255, 150, 0))
            glow_surf.set_alpha(100)
            
            x = SCREEN_WIDTH // 2
            y = 120
            
            for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                screen.blit(glow_surf, (x - text_surf.get_width()//2 + offset[0], 
                                       y + offset[1]))
            
            screen.blit(text_surf, (x - text_surf.get_width()//2, y))
    
    def get_multiplier(self):
        return 1 + (self.combo - 1) * 0.5 if self.combo > 0 else 1

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⚡ NEON ASSAULT ⚡")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_small = pygame.font.Font(None, 28)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_large = pygame.font.Font(None, 72)
        self.font_xlarge = pygame.font.Font(None, 96)
        
        self.high_score = 0
        self.reset_game()

    def reset_game(self):
        self.running = True
        self.game_active = True
        self.score = 0
        # Ensure player is reset if it exists
        if hasattr(self, 'player'):
            self.player.health = 3
            self.player.invulnerability_timer = 0
            self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
            self.player.velocity = pygame.math.Vector2(0, 0)
            
        self.kills = 0
        self.shake_timer = 0
        self.shake_intensity = 1.0
        
        # Groups
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        # Stars
        for _ in range(80):
            Star(self.all_sprites, LAYER_STAR)
            
        self.player = Player(self.all_sprites, self.bullets)
        
        # Spawning
        self.enemy_timer = 0
        self.enemy_spawn_rate = 0.8
        self.powerup_timer = 0
        self.powerup_spawn_rate = 15.0
        
        # Combo system
        self.combo = ComboDisplay()
        
        # Wave system
        self.wave = 1
        self.wave_timer = 0
        self.wave_announce_timer = 0

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            if self.game_active:
                self.update(dt)
            self.draw()
            
    def draw_health(self):
        """Draw player health bar or hearts"""
        if not self.game_active: return
        
        # Draw Hearts
        for i in range(self.player.max_health):
            x = 20 + i * 35
            y = SCREEN_HEIGHT - 40
            
            color = (255, 50, 50) if i < self.player.health else (50, 20, 20)
            
            # Draw Heart Shape
            surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (10, 10), 10)
            pygame.draw.circle(surf, color, (20, 10), 10)
            pygame.draw.polygon(surf, color, [(0, 15), (30, 15), (15, 30)])
            
            self.screen.blit(surf, (x, y))

    def draw(self):
        # ... existing draw code ...
        # (Assuming I'm replacing the end of the run loop or inserting into draw)
        # But wait, the tool requires me to replace existing content.
        # I need to see where 'def draw(self):' is to append this properly.
        # It's not shown in the previous view_file fully.
        # I'll rely on what I saw. It was not fully visible.
        # I will inject draw_health call into the main draw method if I can find it.
        # Actually I can't see the full draw method in the previous 800 lines view.
        # The view_file stopped at line 800.
        # I should read the rest of the file first to be safe,
        # OR I can insert draw_health before draw and then I need to modify draw.
        # Let's read the rest of the file first.
        pass
            
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if not self.game_active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()

    def update(self, dt):
        try:
            self.spawn_enemies(dt)
            self.spawn_powerups(dt)
            self.all_sprites.update(dt)
            self.combo.update(dt)
            
            # Screen shake decay
            if self.shake_timer > 0:
                self.shake_timer -= dt
            
            # Enemy trails
            for enemy in list(self.enemies):
                if random.random() < 0.3:
                    TrailParticle(self.all_sprites, enemy.rect.centerx, enemy.rect.centery,
                                (255, 0, 255), size=3)
            
            # Bullet-Enemy collision
            hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True, 
                                             pygame.sprite.collide_mask)
            for enemy, bullet_list in hits.items():
                try:
                    if enemy.take_damage():
                        # Store enemy data before killing
                        enemy_type = enemy.enemy_type
                        enemy_x = enemy.rect.centerx
                        enemy_y = enemy.rect.centery
                        enemy.kill()
                        self.on_enemy_killed_with_data(enemy_type, enemy_x, enemy_y)
                except Exception as e:
                    print(f"Error in bullet collision: {e}")
                    continue
            
            # Player-PowerUp collision
            powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for powerup in powerup_hits:
                try:
                    self.player.activate_powerup(powerup.powerup_type)
                    self.trigger_shake(0.15, 0.5)
                    
                    # Celebration particles
                    for _ in range(20):
                        Particle(self.all_sprites, powerup.rect.centerx, powerup.rect.centery,
                                powerup.config.color, size_range=(3, 7), speed_range=(100, 300))
                except Exception as e:
                    print(f"Error in powerup collision: {e}")
                    continue
            
            # Player-Enemy collision
            if not self.player.has_shield:
                enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False, 
                                                         pygame.sprite.collide_mask)
                for enemy in enemy_hits:
                    if self.player.take_damage():
                        self.game_over()
                    else:
                        # Player got hurt but survived
                        self.trigger_shake(0.4, 2.0)
                        enemy.kill() # Destroy enemy that hit us
                        
                        # Hurt particles
                        for _ in range(15):
                            Particle(self.all_sprites, self.player.rect.centerx, self.player.rect.centery,
                                   (255, 50, 50), size_range=(3, 6), speed_range=(100, 200))
            else:
                # Shield deflects enemies
                enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, True, 
                                                         pygame.sprite.collide_mask)
                for enemy in enemy_hits:
                    try:
                        self.trigger_shake(0.3, 1.5)
                        for _ in range(25):
                            Particle(self.all_sprites, enemy.rect.centerx, enemy.rect.centery,
                                   COLOR_POWERUP_SHIELD, size_range=(4, 8), speed_range=(150, 350))
                    except Exception as e:
                        print(f"Error in shield collision: {e}")
                        continue
        except Exception as e:
            print(f"Error in update: {e}")
            import traceback
            traceback.print_exc()

    def on_enemy_killed_with_data(self, enemy_type, x, y):
        """Handle enemy death"""
        self.kills += 1
        self.combo.add_kill()
        
        # Score with combo multiplier - bosses worth more
        if enemy_type == "boss":
            base_score = 500
        elif enemy_type == "tank":
            base_score = 200
        elif enemy_type == "fast":
            base_score = 150
        else:
            base_score = 100
            
        self.score += int(base_score * self.combo.get_multiplier())
        
        # More intense shake for bosses
        shake_duration = 0.5 if enemy_type == "boss" else 0.25
        shake_intensity = 2.0 if enemy_type == "boss" else 1.0
        self.trigger_shake(shake_duration, shake_intensity)
        
        # Explosion particles - more for bosses
        if enemy_type == "boss":
            color = (200, 0, 150)
            particle_count = 60
        elif enemy_type == "tank":
            color = (200, 0, 200)
            particle_count = 30
        elif enemy_type == "fast":
            color = (255, 50, 255)
            particle_count = 15
        else:
            color = (255, 0, 255)
            particle_count = 20
        
        for _ in range(particle_count):
            Particle(self.all_sprites, x, y,
                    color, size_range=(3, 8), speed_range=(100, 400), life_range=(0.4, 1.0))

    def spawn_enemies(self, dt):
        self.enemy_timer += dt
        if self.enemy_timer >= self.enemy_spawn_rate:
            self.enemy_timer = 0
            
            # Difficulty scaling
            speed_mod = (self.score // 1000) * 40
            
            # Enemy type distribution
            roll = random.random()
            if roll < 0.65:  # 65% normal enemies
                enemy_type = "normal"
            elif roll < 0.85:  # 20% fast enemies
                enemy_type = "fast"
            elif roll < 0.97:  # 12% tank enemies
                enemy_type = "tank"
            else:  # 3% boss enemies
                enemy_type = "boss"
            
            enemy = Enemy(self.all_sprites, speed_modifier=speed_mod, enemy_type=enemy_type)
            self.enemies.add(enemy)
            
            # Progressive spawn rate increase (caps at 0.25s)
            target_rate = max(0.25, 0.8 - (self.score / 8000.0))
            self.enemy_spawn_rate = target_rate

    def spawn_powerups(self, dt):
        self.powerup_timer += dt
        if self.powerup_timer >= self.powerup_spawn_rate:
            self.powerup_timer = 0
            
            powerup_type = random.choice(list(PowerUpType))
            x = random.randint(60, SCREEN_WIDTH - 60)
            powerup = PowerUp(self.all_sprites, x, -30, powerup_type)
            self.powerups.add(powerup)

    def trigger_shake(self, duration, intensity=1.0):
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_intensity = intensity

    def game_over(self):
        self.game_active = False
        if self.score > self.high_score:
            self.high_score = self.score
        
        # Death explosion
        for _ in range(50):
            Particle(self.all_sprites, self.player.rect.centerx, self.player.rect.centery,
                    (0, 255, 255), size_range=(4, 12), speed_range=(100, 500), life_range=(0.5, 1.5))

    def draw(self):
        try:
            # Screen shake
            offset_x, offset_y = 0, 0
            if self.shake_timer > 0:
                intensity = int(8 * self.shake_intensity)
                offset_x = random.randint(-intensity, intensity)
                offset_y = random.randint(-intensity, intensity)
                
            self.screen.fill(COLOR_BG)
            
            # Draw with shake
            if self.shake_timer > 0:
                shake_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                shake_surf.fill(COLOR_BG)
                self.all_sprites.draw(shake_surf)
                
                # Draw HP bars for bosses on shake surface
                for enemy in list(self.enemies):  # Use list() to avoid iteration issues
                    try:
                        if hasattr(enemy, 'enemy_type') and enemy.enemy_type == "boss":
                            enemy.draw_hp_bar(shake_surf)
                    except:
                        pass  # Skip if enemy is being removed
                
                self.screen.blit(shake_surf, (offset_x, offset_y))
            else:
                self.all_sprites.draw(self.screen)
                
                # Draw HP bars for bosses
                for enemy in list(self.enemies):  # Use list() to avoid iteration issues
                    try:
                        if hasattr(enemy, 'enemy_type') and enemy.enemy_type == "boss":
                            enemy.draw_hp_bar(self.screen)
                    except:
                        pass  # Skip if enemy is being removed

            # UI
            self.draw_ui()
            
            if not self.game_active:
                self.draw_game_over()
                
            pygame.display.flip()
        except Exception as e:
            print(f"Error in draw: {e}")
            import traceback
            traceback.print_exc()
            # Try to continue anyway
            pygame.display.flip()

    def draw_ui(self):
        """Draw game UI"""
        # Score
        score_text = f"SCORE: {self.score:,}"
        score_surf = self.font_medium.render(score_text, True, (255, 255, 255))
        score_surf_shadow = self.font_medium.render(score_text, True, (100, 100, 100))
        self.screen.blit(score_surf_shadow, (12, 12))
        self.screen.blit(score_surf, (10, 10))
        
        # High Score
        high_text = f"HIGH: {self.high_score:,}"
        high_surf = self.font_small.render(high_text, True, (255, 215, 0))
        self.screen.blit(high_surf, (10, 55))
        
        # Kills
        kills_text = f"KILLS: {self.kills}"
        kills_surf = self.font_small.render(kills_text, True, (255, 100, 100))
        self.screen.blit(kills_surf, (10, 85))
        
        # Combo
        self.combo.draw(self.screen)
        
        # Power-up indicators
        y_offset = SCREEN_HEIGHT - 60
        for i, (powerup_type, time_left) in enumerate(self.player.active_powerups.items()):
            config = POWERUP_CONFIGS[powerup_type]
            
            # Background bar
            bar_width = 150
            bar_height = 20
            x = SCREEN_WIDTH - bar_width - 20
            y = y_offset - i * 35
            
            pygame.draw.rect(self.screen, (50, 50, 50), (x, y, bar_width, bar_height))
            
            # Progress bar
            progress = time_left / config.duration
            pygame.draw.rect(self.screen, config.color, 
                           (x, y, int(bar_width * progress), bar_height))
            
            # Label
            label = f"{config.symbol} {time_left:.1f}s"
            label_surf = self.font_small.render(label, True, (255, 255, 255))
            self.screen.blit(label_surf, (x + 5, y - 2))

        # Draw Health Hearts
        if hasattr(self.player, 'max_health'):
            for i in range(self.player.max_health):
                x = 20 + i * 35
                y = SCREEN_HEIGHT - 40
                
                # Active vs Empty
                if i < self.player.health:
                    color = (255, 50, 50) 
                    glow = True
                else:
                    color = (80, 20, 20)
                    glow = False
                
                # Draw Heart Shape
                heart_size = 30
                surf = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
                
                # Points for heart
                pygame.draw.circle(surf, color, (9, 9), 9)
                pygame.draw.circle(surf, color, (21, 9), 9)
                pygame.draw.polygon(surf, color, [(0, 14), (30, 14), (15, 30)])
                
                if glow:
                    # Subtle pulse
                    scale = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() / 300 + i)
                    new_size = int(heart_size * scale)
                    surf = pygame.transform.scale(surf, (new_size, new_size))
                    
                    # Centering offset
                    offset = (heart_size - new_size) // 2
                    self.screen.blit(surf, (x + offset, y + offset))
                else:
                    self.screen.blit(surf, (x, y))

    def draw_game_over(self):
        """Draw game over screen"""
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # GAME OVER with glow
        go_text = "GAME OVER"
        go_surf_glow = self.font_xlarge.render(go_text, True, (255, 50, 50))
        go_surf_glow.set_alpha(100)
        go_surf = self.font_xlarge.render(go_text, True, (255, 100, 100))
        
        go_rect = go_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
        
        # Glow effect
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            self.screen.blit(go_surf_glow, (go_rect.x + dx, go_rect.y + dy))
        self.screen.blit(go_surf, go_rect)
        
        # Final score
        final_text = f"Final Score: {self.score:,}"
        final_surf = self.font_large.render(final_text, True, (255, 255, 255))
        final_rect = final_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(final_surf, final_rect)
        
        # Kills
        kills_text = f"Enemies Destroyed: {self.kills}"
        kills_surf = self.font_medium.render(kills_text, True, (255, 200, 200))
        kills_rect = kills_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(kills_surf, kills_rect)
        
        # High score notification
        if self.score == self.high_score and self.score > 0:
            new_high_text = "★ NEW HIGH SCORE! ★"
            new_high_surf = self.font_large.render(new_high_text, True, (255, 215, 0))
            new_high_rect = new_high_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
            
            # Pulse effect
            pulse = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() / 200)
            new_high_surf = pygame.transform.scale(new_high_surf, 
                                                   (int(new_high_surf.get_width() * pulse),
                                                    int(new_high_surf.get_height() * pulse)))
            new_high_rect = new_high_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
            self.screen.blit(new_high_surf, new_high_rect)
        
        # Restart instruction
        restart_text = "Press 'R' to Restart"
        restart_surf = self.font_medium.render(restart_text, True, (200, 200, 200))
        restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        
        # Blink effect
        if (pygame.time.get_ticks() // 500) % 2:
            self.screen.blit(restart_surf, restart_rect)

if __name__ == "__main__":
    game = Game()
    game.run()