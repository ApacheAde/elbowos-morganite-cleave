#!/usr/bin/env python3
"""Morganite Cleave — neon gem-slash arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "MORGANITE CLEAVE"
HANDLE = "x.com/ElbowOS"

VOID = (14, 6, 18)
PLUM = (42, 12, 36)
ROSE = (255, 92, 168)
PINK = (255, 160, 210)
GOLD = (255, 214, 72)
CREAM = (255, 244, 236)
VIOLET = (176, 88, 255)
CYAN = (72, 240, 255)
INK = (28, 8, 22)
ASH = (90, 70, 88)

PLAY = pygame.Rect(36, 190, W - 72, H - 420)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=4):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Gem:
    __slots__ = ("x", "y", "vx", "vy", "kind", "rot", "spin", "r", "alive", "pts")

    def __init__(self, x, y, vx, vy, kind):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.kind = kind  # rose / gold / violet / ash
        self.rot = random.uniform(0, 6.28)
        self.spin = random.uniform(-4.2, 4.2)
        self.r = 38 if kind != "ash" else 34
        self.alive = True
        self.pts = {"rose": 12, "gold": 22, "violet": 18, "ash": -18}[kind]


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 62)
        self.font_md = pygame.font.Font(None, 48)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()
        self.screen = None
        if not record:
            self.screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption(TITLE)

    def reset(self) -> None:
        self.t = 0.0
        self.score = 0
        self.combo = 0
        self.combo_cd = 0.0
        self.flash = 0.0
        self.gems: list[Gem] = []
        self.sparks: list[Spark] = []
        self.pops: list[tuple[str, float, float, float, tuple]] = []
        self.slash: list[tuple[float, float, float]] = []
        self.blade = (W * 0.5, H * 0.55)
        self.bvx = 0.0
        self.bvy = 0.0
        self.spawn_cd = 0.15
        self.stars = [(random.randint(0, W), random.randint(0, H), random.random()) for _ in range(90)]
        self.petals = [(random.uniform(0, W), random.uniform(0, H), random.uniform(12, 40)) for _ in range(18)]
        self.alive = True
        self.running = True
        self.slicing = False

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            a = random.uniform(0, 6.28)
            sp = random.uniform(90, 520)
            self.sparks.append(Spark(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                     random.uniform(0.18, 0.5), col, random.randint(3, 7)))

    def launch(self) -> None:
        side = random.choice((-1, 1))
        x = PLAY.centerx + side * random.uniform(40, 360)
        y = PLAY.bottom + 20
        vx = -side * random.uniform(80, 280) + random.uniform(-40, 40)
        vy = -random.uniform(980, 1320)
        roll = random.random()
        if roll < 0.12:
            kind = "ash"
        elif roll < 0.32:
            kind = "gold"
        elif roll < 0.55:
            kind = "violet"
        else:
            kind = "rose"
        self.gems.append(Gem(x, y, vx, vy, kind))

    def want_target(self) -> tuple[float, float] | None:
        live = [g for g in self.gems if g.alive and PLAY.top < g.y < PLAY.bottom - 40]
        goods = [g for g in live if g.kind != "ash"]
        if not goods:
            return None
        goods.sort(key=lambda g: g.y)
        g = goods[len(goods) // 2] if len(goods) > 2 else goods[0]
        return g.x, g.y

    def try_slash(self, x, y) -> None:
        self.slash.append((x, y, 0.22))
        hit = 0
        for g in self.gems:
            if not g.alive:
                continue
            if math.hypot(g.x - x, g.y - y) < g.r + 26:
                g.alive = False
                hit += 1
                col = {"rose": ROSE, "gold": GOLD, "violet": VIOLET, "ash": ASH}[g.kind]
                self.burst(g.x, g.y, col, 18 if g.kind != "ash" else 10)
                if g.kind == "ash":
                    self.combo = 0
                    self.score = max(0, self.score + g.pts)
                    self.flash = 0.28
                    self.pops.append(("SHARD", g.x, g.y - 30, 0.7, ASH))
                else:
                    self.combo += 1
                    self.combo_cd = 0.85
                    add = g.pts + self.combo * 3
                    self.score += add
                    self.pops.append((f"+{add}", g.x, g.y - 24, 0.55, GOLD))
        if hit == 0:
            self.combo_cd = max(0.0, self.combo_cd - 0.04)

    def update(self, dt: float) -> None:
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.combo_cd = max(0.0, self.combo_cd - dt)
        if self.combo_cd <= 0:
            self.combo = 0
        self.spawn_cd -= dt
        rate = max(0.18, 0.55 - self.t * 0.018)
        if self.spawn_cd <= 0:
            self.launch()
            if random.random() < 0.35:
                self.launch()
            self.spawn_cd = rate
        g = 980.0
        live_g = []
        for gem in self.gems:
            gem.vy += g * dt
            gem.x += gem.vx * dt
            gem.y += gem.vy * dt
            gem.rot += gem.spin * dt
            if gem.alive and gem.y < PLAY.bottom + 80:
                live_g.append(gem)
        self.gems = live_g[-40:]
        if self.record:
            tgt = self.want_target()
            if tgt:
                tx, ty = tgt
                self.bvx = (tx - self.blade[0]) * 9.0
                self.bvy = (ty - self.blade[1]) * 9.0
                self.blade = (self.blade[0] + self.bvx * dt, self.blade[1] + self.bvy * dt)
                if math.hypot(tx - self.blade[0], ty - self.blade[1]) < 70:
                    self.try_slash(tx, ty)
                    self.blade = (tx, ty)
            else:
                self.blade = (
                    PLAY.centerx + math.sin(self.t * 1.7) * 280,
                    PLAY.centery + math.cos(self.t * 1.1) * 180,
                )
                self.slash.append((self.blade[0], self.blade[1], 0.12))
        self.slash = [(x, y, l - dt) for x, y, l in self.slash if l - dt > 0][-70:]
        live_s = []
        for sp in self.sparks:
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt + 220 * dt
            sp.life -= dt
            if sp.life > 0:
                live_s.append(sp)
        self.sparks = live_s[-220:]
        self.pops = [(a, x, y - 80 * dt, life - dt, c) for a, x, y, life, c in self.pops if life - dt > 0]

    def gem_poly(self, g: Gem) -> list[tuple[int, int]]:
        n = 4 if g.kind == "gold" else (6 if g.kind == "violet" else (3 if g.kind == "ash" else 5))
        pts = []
        for i in range(n):
            a = g.rot + i * (6.28318 / n)
            rr = g.r if i % 2 == 0 else g.r * 0.62
            pts.append((int(g.x + math.cos(a) * rr), int(g.y + math.sin(a) * rr)))
        return pts

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        for sx, sy, tw in self.stars:
            yy = int((sy + self.t * (10 + tw * 22)) % H)
            c = 40 + int(tw * 80)
            pygame.draw.circle(s, (c, int(c * 0.55), int(c * 0.85)), (sx, yy), 1 + int(tw * 2))
        for px, py, pr in self.petals:
            yy = (py + self.t * 28) % H
            xx = px + math.sin(self.t * 0.7 + px) * 18
            pygame.draw.circle(s, (60, 16, 40), (int(xx), int(yy)), int(pr * 0.35), 1)
        pygame.draw.rect(s, PLUM, PLAY, border_radius=32)
        pygame.draw.rect(s, ROSE, PLAY, 4, border_radius=32)
        pygame.draw.rect(s, PINK, PLAY, 2, border_radius=32)
        for gem in self.gems:
            if not gem.alive:
                continue
            col = {"rose": ROSE, "gold": GOLD, "violet": VIOLET, "ash": ASH}[gem.kind]
            poly = self.gem_poly(gem)
            pygame.draw.polygon(s, col, poly)
            pygame.draw.polygon(s, CREAM, poly, 3)
            pygame.draw.circle(s, CREAM, (int(gem.x), int(gem.y)), 5)
        pts = [(int(x), int(y)) for x, y, _ in self.slash]
        if len(pts) > 1:
            pygame.draw.lines(s, ROSE, False, pts, 10)
            pygame.draw.lines(s, CREAM, False, pts, 3)
        bx, by = int(self.blade[0]), int(self.blade[1])
        pygame.draw.circle(s, GOLD, (bx, by), 14)
        pygame.draw.circle(s, CREAM, (bx, by), 6)
        for sp in self.sparks:
            a = max(20, int(255 * sp.life / 0.5))
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life / 0.4)))
        if self.flash > 0:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 60, 90, int(90 * self.flash / 0.28)))
            s.blit(veil, (0, 0))
        title = self.font_lg.render(TITLE, True, ROSE)
        s.blit(title, title.get_rect(center=(W // 2, 56)))
        handle = self.font_sm.render(HANDLE, True, PINK)
        s.blit(handle, handle.get_rect(center=(W // 2, 108)))
        s.blit(self.font_md.render(f"SCORE  {self.score}", True, GOLD), (64, 1768))
        s.blit(self.font_md.render(f"COMBO  x{self.combo}", True, CYAN), (W - 340, 1768))
        hint = self.font_sm.render("slash rose quartz — spare the ash shards", True, CREAM)
        s.blit(hint, hint.get_rect(center=(W // 2, 1830)))
        for tag, x, y, life, col in self.pops:
            img = self.font_md.render(tag, True, col)
            s.blit(img, img.get_rect(center=(int(x), int(y))))
        foot = self.font_sm.render("DRAG to cleave     R reset     ESC quit", True, (200, 140, 180))
        s.blit(foot, foot.get_rect(center=(W // 2, H - 24)))

    def handle(self, ev) -> None:
        if ev.type == pygame.QUIT:
            self.running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.running = False
            elif ev.key == pygame.K_r:
                self.reset()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.slicing = True
            self.blade = ev.pos
            self.try_slash(*ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.slicing = False
        elif ev.type == pygame.MOUSEMOTION and self.slicing:
            self.blade = ev.pos
            self.try_slash(*ev.pos)

    def play(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            self.screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    if record:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record)
    if record:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/MORGANITE_CLEAVE_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
