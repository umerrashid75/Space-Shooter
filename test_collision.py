import pygame
import unittest

# Initialize pygame (needed for Surface and Mask)
pygame.init()

class TestMaskCollision(unittest.TestCase):
    def setUp(self):
        # Create a simplified sprite class
        class TestSprite(pygame.sprite.Sprite):
            def __init__(self, size, color, shape_draw_func):
                super().__init__()
                self.image = pygame.Surface(size, pygame.SRCALPHA)
                shape_draw_func(self.image)
                self.rect = self.image.get_rect()
                self.mask = pygame.mask.from_surface(self.image)
        
        self.TestSprite = TestSprite

    def test_rect_overlap_but_no_mask_collision(self):
        """
        Test two objects whose Rects overlap but pixels do not.
        Imagine two triangles pointing away from each other or just being offset.
        Let's use 10x10 surfaces.
        """
        # Sprite A: Top-Left pixel only
        def draw_a(surf):
            surf.set_at((0, 0), (255, 255, 255, 255))
        
        # Sprite B: Bottom-Right pixel only
        def draw_b(surf):
            surf.set_at((9, 9), (255, 255, 255, 255))

        sprite_a = self.TestSprite((10, 10), None, draw_a)
        sprite_b = self.TestSprite((10, 10), None, draw_b)
        
        # Position them at effectively the same place, so Rects perfectly overlap
        sprite_a.rect.topleft = (0, 0)
        sprite_b.rect.topleft = (0, 0)
        
        # RECT collision should be True
        self.assertTrue(pygame.sprite.collide_rect(sprite_a, sprite_b), "Rects should collide")
        
        # MASK collision should be False
        self.assertFalse(pygame.sprite.collide_mask(sprite_a, sprite_b), "Masks should NOT collide")

    def test_mask_collision_true(self):
        """Test actual pixel overlap."""
        # Sprite A: Center pixel
        def draw_a(surf):
            surf.set_at((5, 5), (255, 255, 255, 255))
            
        sprite_a = self.TestSprite((10, 10), None, draw_a)
        sprite_b = self.TestSprite((10, 10), None, draw_a) # Identical
        
        sprite_a.rect.topleft = (0, 0)
        sprite_b.rect.topleft = (0, 0)
        
        self.assertTrue(pygame.sprite.collide_mask(sprite_a, sprite_b), "Masks should collide")

if __name__ == '__main__':
    unittest.main()
