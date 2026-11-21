# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/androyesfernandez/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/androyesfernandez/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A deterministic, standard-library-only Python program that draws a one-page newspaper poster summing up the world news of Friday 20 November 2026, and writes it to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`). Six cross-verified stories of that day — Cyclone Akvan's landfall in Odisha, the AI rout that sank Asian markets and then Wall Street, COP31 running into overtime in Antalya, the overnight strikes on Kyiv, Saudi defences downing four Houthi missiles, and the EU–UK summit in Brussels — rendered pixel by pixel with an embedded bitmap font. The page carries 46 numbered stories across all eight regions (including Oceania), a UTC timeline of the day, the day's six big numbers, a dotted world map with numbered pins, and a red DATE CHECK box excluding the previous day's news. No network, no clock, no randomness: every run produces byte-identical output (1024×1024 PNG, ~48 KB).

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/output python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=ktpzxevq&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
