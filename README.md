# ⚡ NEON ASSAULT ⚡

A high-octane, neon-drenched space shooter built with Python and Pygame. detailed particle effects, screen shake, and intense arcade action.

![Neon Assault Gameplay Placeholder](https://via.placeholder.com/800x450?text=Neon+Assault+Gameplay)

## ✨ Features

-   **Dynamic Combat**: Smooth controls with inertia-based movement.
-   **Neon Aesthetics**: Glowing visuals, particle trails, and vibrant color palettes.
-   **Enemy Variety**:
    -   **Normal**: Standard fighter drones.
    -   **Fast**: Agile interceptors that are hard to hit.
    -   **Tank**: Heavily armored ships that take a beating.
    -   **Boss**: Massive capital ships with high HP and distinct visual designs.
-   **Power-Up System**:
    -   **⚡ Rapid Fire**: drastically increases fire rate.
    -   **⊕ Spread Shot**: Fires 3 bullets at once covering a wide angle.
    -   **◆ Shield**: Grants temporary invulnerability and deflects enemies.
-   **Juice**: Screen shake, impact frames, muzzle flashes, and explosive particle effects.
-   **Health System**: 3-Heart health system with invulnerability frames.
-   **Scoring & Combos**: Chain kills together to build your combo multiplier and chase the high score.

## 🎮 Controls

| Action | Keyboard | Mouse |
| :--- | :--- | :--- |
| **Move** | `W`, `A`, `S`, `D` or `Arrow Keys` | - |
| **Shoot** | `Spacebar` | `Left Click` |
| **Restart** | `R` (on Game Over screen) | - |
| **Quit** | `Escape` or `Close Window` | - |

## 🛠️ Installation & Running

1.  **Prerequisites**:
    -   Python 3.10+ installed.
    -   `pygame` library.

2.  **Install Dependencies**:
    ```bash
    pip install pygame
    ```

3.  **Run the Game**:
    ```bash
    python main.py
    ```

    *Note: If you have multiple Python versions, you might need to use `py -3.12 main.py` or `python3 main.py`.*

## 🔧 Technical Details

-   **Engine**: Pygame (SDL wrapper for Python).
-   **Collision**: Pixel-perfect mask collision for precise hitboxes.
-   **Rendering**: Custom transparency and additive blending for glow effects.
-   **Structure**:
    -   `Game`: Main loop and state management.
    -   `Player` / `Enemy`: Entity classes with physics and AI.
    -   `Particle`: System for visual effects.

---

*Created for the Pygame Community. Enjoy the chaos!*
