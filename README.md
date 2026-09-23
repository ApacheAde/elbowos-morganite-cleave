# Morganite Cleave

Full-colour **Python 3** neon gem-slash arcade for [ElbowOS](https://x.com/ElbowOS).

Rose, gold and violet quartz launch in arcs. Drag to cleave them. Ash shards break the combo.

## Play

```
pip install -r requirements.txt
python3 morganite_cleave.py --play
```

Drag across gems. `R` resets. `ESC` quits.

If you launch with no flags on a desktop it also opens the window (omit `--record`).

## Record a 9:16 reel

```
python3 morganite_cleave.py --record
```

Writes `/home/workdir/artifacts/MORGANITE_CLEAVE_ElbowOS.mp4` (1080×1920, 15s, 30fps, h264).

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/18aivXiEQ7luUBwl-gQoaP0iuPSBSqDY8/view

## Controls

| Input | Action |
| --- | --- |
| Drag / mouse | slash |
| R | reset |
| ESC | quit |
