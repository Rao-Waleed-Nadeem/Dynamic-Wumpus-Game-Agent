# WUMPUS — Dynamic Logic Agent

> A Knowledge-Based Agent navigating a Wumpus World using Propositional Logic and Resolution Refutation.

---

## Overview

This project implements a fully-functional **Knowledge-Based Agent** that navigates a dynamic Wumpus World grid. The agent perceives its environment, maintains a **Propositional Logic Knowledge Base (KB)**, and uses **Resolution Refutation** to prove whether adjacent cells are safe before moving.

The system is split into:

- **Python Backend** — Game engine, KB, and inference engine (Flask REST API)
- **Web Frontend** — Extraordinary dark-theme UI with real-time metrics dashboard

---

## Architecture

```
wumpus/
├── backend/
│   ├── wumpus_engine.py     # Core engine: World, Agent, KB, Resolution
│   ├── app.py               # Flask REST API
│   └── requirements.txt
└── frontend/
    └── index.html           # Self-contained web app
```

---

## Algorithmic Implementation

### Knowledge Base

The KB stores **CNF clauses** (disjunctions of literals).

**Telling the KB:**

- `BREEZE at (r,c)` → adds clause `P_{n1} ∨ P_{n2} ∨ ...` for each neighbor
- `NO BREEZE at (r,c)` → adds unit clauses `¬P_{n}` for each neighbor
- `STENCH at (r,c)` → adds clause `W_{n1} ∨ W_{n2} ∨ ...` for each neighbor
- `NO STENCH at (r,c)` → adds unit clauses `¬W_{n}` for each neighbor

**Asking the KB (Resolution Refutation):**
To prove `safe(r,c)` = `¬P_{r,c} ∧ ¬W_{r,c}`:

1. Negate the query: add `P_{r,c}` as a unit clause
2. Resolve all clause pairs exhaustively
3. If empty clause `{}` is derived → **contradiction found → ¬P proven**
4. Repeat for `W_{r,c}`
5. Both proven → cell is **SAFE**

### Resolution Algorithm

```python
def resolve(c1, c2):
    for lit in c1:
        if negate(lit) in c2:
            resolvent = (c1 - {lit}) | (c2 - {negate(lit)})
            if not is_tautology(resolvent):
                return resolvent
    return None

def resolution_refutation(kb, query):
    clauses = kb ∪ {¬query}
    while True:
        new = ∅
        for (c1, c2) in all_pairs(clauses):
            r = resolve(c1, c2)
            if r == {} (empty): return PROVED
            if r: new.add(r)
        if new ⊆ clauses: return UNPROVABLE
        clauses = clauses ∪ new
```

**Complexity:** O(2^n) worst case — complete and sound for propositional logic.

---

## API Endpoints

| Method | Endpoint      | Description                                    |
| ------ | ------------- | ---------------------------------------------- |
| POST   | `/api/new`    | Initialize new episode `{rows, cols, numPits}` |
| GET    | `/api/state`  | Get current game state                         |
| POST   | `/api/move`   | Move agent `{direction: UP/DOWN/LEFT/RIGHT}`   |
| POST   | `/api/shoot`  | Shoot arrow `{direction}`                      |
| POST   | `/api/climb`  | Climb out of cave                              |
| POST   | `/api/auto`   | Autonomous agent step                          |
| GET    | `/api/reveal` | Reveal true world (debug)                      |

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
# Flask server starts on http://localhost:5000
```

### 2. Frontend

Open `frontend/index.html` in any browser.
_(No build step required — pure HTML/CSS/JS)_

---

## Controls

| Key     | Action           |
| ------- | ---------------- |
| ↑ ↓ ← → | Move agent       |
| W A S D | Move agent       |
| C       | Climb out        |
| Space   | Auto-step once   |
| N       | New game         |
| P       | Toggle auto-play |

---

## Scoring

| Event               | Points |
| ------------------- | ------ |
| Each step           | −1     |
| Shoot arrow         | −10    |
| Fall in pit / eaten | −1000  |
| Kill Wumpus         | +500   |
| Pick up gold        | +1000  |
| Climb out with gold | +500   |

---

## Environment Specifications

- **Dynamic grid sizing**: 2×2 to 8×8
- **Dynamic hazards**: Pits and Wumpus randomly placed each episode
- **Percepts**:
  - `BREEZE` — adjacent to pit
  - `STENCH` — adjacent to Wumpus
  - `GLITTER` — gold in current cell
  - `SCREAM` — Wumpus killed by arrow

---

## Agent Decision Policy

The autonomous agent follows this priority:

1. Move to an **unvisited safe** neighbor (proven by KB)
2. BFS backtrack to reach a safe frontier
3. Climb out (if gold collected or no safe moves remain)

---

## Technologies

- **Python 3.10+** — Game engine and inference
- **Flask** — REST API
- **Vanilla JS** — Frontend (zero dependencies)
- **CSS Custom Properties** — Theming system
- **Space Mono + Syne** — Typography

---

## Key Features

- ✅ Complete Resolution Refutation in pure Python
- ✅ CNF clause management
- ✅ Real-time KB clause visualization
- ✅ Inference step counter
- ✅ Percept display per cell
- ✅ Safe/Unknown/Danger/Pit/Wumpus cell coloring
- ✅ Agent token with animation
- ✅ World reveal overlay
- ✅ Auto-play with BFS pathfinding
- ✅ Keyboard controls
- ✅ Cell tooltips
- ✅ Score tracking
- ✅ Responsive grid sizing

---

_Built for competitive showcase — hackathon and portfolio ready._
