# XP and Coins System

## Global XP

XP is global to the user, not tied to a specific project or activity.

```text
User
├── Total XP
└── Level
```

XP never decreases.

### Levels

Use a progressively increasing XP requirement.

```text
XP needed for next level = 100 × Level^1.5
```

Example:

| Level | XP needed |
| ----: | --------: |
| 1 → 2 |       100 |
| 2 → 3 |       283 |
| 3 → 4 |       520 |
| 4 → 5 |       800 |
| 5 → 6 |     1,118 |

---

## Sprint XP

Every completed sprint gives XP.

```text
Sprint XP = Participation XP + Progress XP
```

### Participation XP

Completing the sprint always gives:

```text
10 XP
```

If the user participates without registering a word count:

```text
10 XP
0 coins
```

This lets non-word-count activities participate without inventing progress.

### Progress XP

For writing:

```text
Progress XP = positive words written × difficulty multiplier
```

Base rate:

```text
100 words = 5 XP
```

Only **positive progress** counts.

```text
Start: 1,000
End:   1,300
Progress: +300

→ XP for 300 words
```

But:

```text
Start: 1,000
End:   800
Progress: -200

→ 0 progress XP
→ 0 coins
→ still receives participation XP
```

Negative word counts never remove XP or coins.

---

## Sprint Complexity

The sprint can modify the reward according to its complexity.

| Complexity | Multiplier |
| ---------- | ---------: |
| Easy       |       ×1.0 |
| Normal     |      ×1.25 |
| Hard       |       ×1.5 |
| Extreme    |       ×2.0 |

Example:

```text
+500 words
Base XP: 25

Hard sprint:
25 × 1.5 = 37.5 XP

Participation: +10 XP

Total: 47.5 XP
```

Round XP to a whole number when awarding it.

---

## Coins

Coins are separate from XP.

```text
User
├── Total XP
├── Level
└── Coins
```

XP represents **long-term progression**.

Coins are a **spendable reward**.

Base writing reward:

```text
100 positive words = 1 coin
```

Then apply the same complexity multiplier:

```text
Coins = base coins × complexity multiplier
```

Round down to a whole coin.

Example:

```text
+650 words
Hard ×1.5

Base coins = 6.5
6.5 × 1.5 = 9.75

Reward = 9 coins
```

---

## Rules

* XP is global.
* Levels are calculated from global XP.
* XP never decreases.
* Coins never decrease because of negative progress.
* Negative word counts give **0 progress XP and 0 progress coins**.
* Completing a sprint always gives the base **participation XP**.
* No word count gives **participation XP only**.
* Complexity increases progress XP and coins.
* Participation XP is not multiplied by complexity.
* Coins are spendable; XP is permanent progression.
