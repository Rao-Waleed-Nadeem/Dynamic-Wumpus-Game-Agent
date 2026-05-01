"""
Wumpus World Knowledge-Based Agent
Resolution Refutation Inference Engine
"""

import random
import itertools
from typing import Set, List, Tuple, Dict, Optional, FrozenSet
from dataclasses import dataclass, field
from enum import Enum


# ─────────────────────────────────────────────
# Data Types
# ─────────────────────────────────────────────

class Percept(str, Enum):
    BREEZE  = "BREEZE"
    STENCH  = "STENCH"
    GLITTER = "GLITTER"
    BUMP    = "BUMP"
    SCREAM  = "SCREAM"

class CellStatus(str, Enum):
    UNKNOWN   = "UNKNOWN"
    SAFE      = "SAFE"
    VISITED   = "VISITED"
    PIT       = "PIT"
    WUMPUS    = "WUMPUS"
    DANGER    = "DANGER"   # inferred possible hazard

# A literal: (name, positive)
# e.g. ("P_1_2", True) = P_1_2; ("P_1_2", False) = ¬P_1_2
Literal = Tuple[str, bool]
Clause  = FrozenSet[Literal]   # disjunction of literals


# ─────────────────────────────────────────────
# CNF / Resolution helpers
# ─────────────────────────────────────────────

def negate(lit: Literal) -> Literal:
    return (lit[0], not lit[1])

def resolve(c1: Clause, c2: Clause) -> Optional[Clause]:
    """
    Standard resolution: if c1 has L and c2 has ¬L, return the resolvent.
    Returns None if no complementary pair found, or if the resolvent is a
    tautology (contains both P and ¬P for some variable).
    """
    for lit in c1:
        neg = negate(lit)
        if neg in c2:
            new_clause = (c1 - {lit}) | (c2 - {neg})
            # check tautology
            for l in new_clause:
                if negate(l) in new_clause:
                    return None
            return frozenset(new_clause)
    return None


def resolution_refutation(kb_clauses: List[Clause], query_lit: Literal) -> Tuple[bool, int]:
    """
    Prove query_lit by refutation: add ¬query_lit to KB, then resolve.
    Returns (proved: bool, inference_steps: int)
    """
    neg_query: Clause = frozenset([negate(query_lit)])
    clause_set: Set[Clause] = set(kb_clauses) | {neg_query}
    steps = 0

    while True:
        new_clauses: Set[Clause] = set()
        clause_list = list(clause_set)

        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                resolvent = resolve(clause_list[i], clause_list[j])
                steps += 1
                if resolvent is not None:
                    if len(resolvent) == 0:          # empty clause → contradiction
                        return True, steps
                    new_clauses.add(resolvent)

        if new_clauses.issubset(clause_set):         # no new clauses → can't prove
            return False, steps

        clause_set |= new_clauses


# ─────────────────────────────────────────────
# Knowledge Base
# ─────────────────────────────────────────────

class KnowledgeBase:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.clauses: List[Clause] = []
        self.total_inference_steps = 0
        self._init_structural_axioms()

    def _cell_var(self, kind: str, r: int, c: int) -> str:
        return f"{kind}_{r}_{c}"

    def _neighbors(self, r: int, c: int) -> List[Tuple[int,int]]:
        out = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                out.append((nr, nc))
        return out

    def _init_structural_axioms(self):
        """No pit/wumpus at start cell (0,0)."""
        self.tell_unit(f"P_0_0", False)
        self.tell_unit(f"W_0_0", False)

    def tell_unit(self, var: str, positive: bool):
        """Assert a unit clause (single literal)."""
        self.clauses.append(frozenset([(var, positive)]))

    def tell_breeze(self, r: int, c: int):
        """
        BREEZE at (r,c)  ⟺  at least one adjacent cell has a pit.
        B_{r,c} → ∨ P_{n} for each neighbor n
        Also: ¬B_{r,c} → ¬P_{n} for each neighbor n
        """
        neighbors = self._neighbors(r, c)
        # B → (P_n1 ∨ P_n2 ∨ ...)
        clause: List[Literal] = []
        for nr, nc in neighbors:
            clause.append((self._cell_var("P", nr, nc), True))
        if clause:
            self.clauses.append(frozenset(clause))

    def tell_no_breeze(self, r: int, c: int):
        """No breeze → no pits in adjacent cells."""
        for nr, nc in self._neighbors(r, c):
            self.tell_unit(self._cell_var("P", nr, nc), False)

    def tell_stench(self, r: int, c: int):
        neighbors = self._neighbors(r, c)
        clause: List[Literal] = []
        for nr, nc in neighbors:
            clause.append((self._cell_var("W", nr, nc), True))
        if clause:
            self.clauses.append(frozenset(clause))

    def tell_no_stench(self, r: int, c: int):
        for nr, nc in self._neighbors(r, c):
            self.tell_unit(self._cell_var("W", nr, nc), False)

    def ask_safe(self, r: int, c: int) -> Tuple[bool, int]:
        """
        Ask: is cell (r,c) safe?
        Prove both ¬P_{r,c} and ¬W_{r,c} via resolution refutation.
        Returns (safe: bool, steps: int)
        """
        no_pit_query   = (self._cell_var("P", r, c), False)   # ¬P
        no_wumpus_query= (self._cell_var("W", r, c), False)   # ¬W

        proved_no_pit,   s1 = resolution_refutation(self.clauses, no_pit_query)
        proved_no_wumpus,s2 = resolution_refutation(self.clauses, no_wumpus_query)

        total = s1 + s2
        self.total_inference_steps += total
        return (proved_no_pit and proved_no_wumpus), total

    def ask_pit(self, r: int, c: int) -> Tuple[bool, int]:
        """Ask: is cell (r,c) definitely a pit?"""
        pit_query = (self._cell_var("P", r, c), True)
        proved, steps = resolution_refutation(self.clauses, pit_query)
        self.total_inference_steps += steps
        return proved, steps

    def ask_wumpus(self, r: int, c: int) -> Tuple[bool, int]:
        """Ask: is cell (r,c) definitely the wumpus?"""
        w_query = (self._cell_var("W", r, c), True)
        proved, steps = resolution_refutation(self.clauses, w_query)
        self.total_inference_steps += steps
        return proved, steps


# ─────────────────────────────────────────────
# World
# ─────────────────────────────────────────────

@dataclass
class WorldState:
    rows: int
    cols: int
    pits: Set[Tuple[int,int]]
    wumpus: Tuple[int,int]
    gold: Tuple[int,int]
    wumpus_alive: bool = True

    def get_percepts(self, r: int, c: int) -> List[str]:
        percepts = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if (nr, nc) in self.pits:
                percepts.append(Percept.BREEZE)
                break
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if self.wumpus_alive and (nr, nc) == self.wumpus:
                percepts.append(Percept.STENCH)
                break
        if (r, c) == self.gold:
            percepts.append(Percept.GLITTER)
        return percepts


# ─────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────

@dataclass
class AgentState:
    row: int = 0
    col: int = 0
    has_arrow: bool = True
    has_gold: bool = False
    alive: bool = True
    score: int = 0
    visited: Set[Tuple[int,int]] = field(default_factory=set)
    cell_status: Dict[Tuple[int,int], str] = field(default_factory=dict)
    move_history: List[Dict] = field(default_factory=list)


# ─────────────────────────────────────────────
# Game Engine  (the main API surface)
# ─────────────────────────────────────────────

class WumpusGame:
    def __init__(self, rows: int = 4, cols: int = 4, pit_probability: float = 0.2,
                 num_pits: Optional[int] = None, seed: Optional[int] = None):
        self.rows = max(2, min(rows, 8))
        self.cols = max(2, min(cols, 8))
        self.pit_prob = pit_probability
        self._seed = seed
        self.num_pits = num_pits
        self.reset()

    # ── initialisation ─────────────────────────────────────────────────────

    def reset(self) -> Dict:
        if self._seed is not None:
            random.seed(self._seed)

        self.world   = self._generate_world()
        self.agent   = AgentState()
        self.kb      = KnowledgeBase(self.rows, self.cols)
        self.game_over = False
        self.won       = False
        self.step_log: List[Dict] = []

        # visit start cell
        return self._visit_current_cell()

    def _generate_world(self) -> WorldState:
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) != (0, 0)]
        random.shuffle(all_cells)

        if self.num_pits is not None:
            n_pits = self.num_pits
        else:
            n_pits = max(1, int(self.rows * self.cols * self.pit_prob))

        pits    = set(all_cells[:n_pits])
        wumpus  = all_cells[n_pits]
        gold_candidates = [c for c in all_cells[n_pits+1:] if c not in pits]
        gold = random.choice(gold_candidates) if gold_candidates else all_cells[-1]

        return WorldState(
            rows=self.rows, cols=self.cols,
            pits=pits, wumpus=wumpus, gold=gold
        )

    # ── core step ──────────────────────────────────────────────────────────

    def _visit_current_cell(self) -> Dict:
        r, c = self.agent.row, self.agent.col
        self.agent.visited.add((r, c))

        # death check
        if (r, c) in self.world.pits:
            self.agent.alive  = False
            self.agent.score -= 1000
            self.game_over    = True
            self.agent.cell_status[(r,c)] = CellStatus.PIT
            return self._build_state(event="FELL_IN_PIT")

        if (r, c) == self.world.wumpus and self.world.wumpus_alive:
            self.agent.alive  = False
            self.agent.score -= 1000
            self.game_over    = True
            self.agent.cell_status[(r,c)] = CellStatus.WUMPUS
            return self._build_state(event="EATEN_BY_WUMPUS")

        # mark visited
        self.agent.cell_status[(r,c)] = CellStatus.VISITED
        self.agent.score -= 1   # step cost

        # percepts
        percepts = self.world.get_percepts(r, c)

        # tell KB
        if Percept.BREEZE in percepts:
            self.kb.tell_breeze(r, c)
        else:
            self.kb.tell_no_breeze(r, c)

        if Percept.STENCH in percepts:
            self.kb.tell_stench(r, c)
        else:
            self.kb.tell_no_stench(r, c)

        # gold
        if Percept.GLITTER in percepts and not self.agent.has_gold:
            self.agent.has_gold = True
            self.agent.score   += 1000

        # infer neighbors
        inference_details = self._infer_neighbors(r, c)

        step_data = self._build_state(
            event="STEP",
            percepts=[p.value for p in percepts],
            inference=inference_details
        )
        self.step_log.append(step_data)
        return step_data

    def _infer_neighbors(self, r: int, c: int) -> List[Dict]:
        results = []
        for nr, nc in self._neighbors(r, c):
            if (nr, nc) in self.agent.visited:
                continue
            safe, steps = self.kb.ask_safe(nr, nc)
            is_pit, ps  = self.kb.ask_pit(nr, nc)
            is_wump,ws  = self.kb.ask_wumpus(nr, nc)

            if safe:
                self.agent.cell_status[(nr,nc)] = CellStatus.SAFE
            elif is_pit:
                self.agent.cell_status[(nr,nc)] = CellStatus.PIT
            elif is_wump:
                self.agent.cell_status[(nr,nc)] = CellStatus.WUMPUS
            else:
                if (nr, nc) not in self.agent.cell_status:
                    self.agent.cell_status[(nr,nc)] = CellStatus.UNKNOWN

            results.append({
                "cell": [nr, nc],
                "safe": safe,
                "pit": is_pit,
                "wumpus": is_wump,
                "steps": steps + ps + ws,
                "status": self.agent.cell_status.get((nr,nc), CellStatus.UNKNOWN)
            })
        return results

    # ── actions ────────────────────────────────────────────────────────────

    def move(self, direction: str) -> Dict:
        if self.game_over:
            return self._build_state(event="GAME_OVER")

        dr, dc = {"UP":(-1,0),"DOWN":(1,0),"LEFT":(0,-1),"RIGHT":(0,1)}.get(direction.upper(),(0,0))
        nr, nc = self.agent.row + dr, self.agent.col + dc

        if not (0 <= nr < self.rows and 0 <= nc < self.cols):
            self.agent.score -= 1
            return self._build_state(event="BUMP")

        self.agent.row, self.agent.col = nr, nc
        return self._visit_current_cell()

    def shoot(self, direction: str) -> Dict:
        if self.game_over:
            return self._build_state(event="GAME_OVER")
        if not self.agent.has_arrow:
            return self._build_state(event="NO_ARROW")

        self.agent.has_arrow = False
        self.agent.score    -= 10

        dr, dc = {"UP":(-1,0),"DOWN":(1,0),"LEFT":(0,-1),"RIGHT":(0,1)}.get(direction.upper(),(0,0))
        r, c   = self.agent.row + dr, self.agent.col + dc

        while 0 <= r < self.rows and 0 <= c < self.cols:
            if (r, c) == self.world.wumpus and self.world.wumpus_alive:
                self.world.wumpus_alive = False
                self.kb.tell_unit(f"W_{r}_{c}", False)   # wumpus dead
                self.agent.cell_status[(r,c)] = CellStatus.SAFE
                self.agent.score += 500
                return self._build_state(event="WUMPUS_KILLED", percepts=[Percept.SCREAM.value])
            r, c = r + dr, c + dc

        return self._build_state(event="ARROW_MISSED")

    def climb(self) -> Dict:
        if self.agent.row == 0 and self.agent.col == 0:
            if self.agent.has_gold:
                self.agent.score += 500
                self.won = True
            self.game_over = True
            return self._build_state(event="CLIMBED_OUT")
        return self._build_state(event="NOT_AT_EXIT")

    def auto_step(self) -> Dict:
        """Agent autonomously picks a safe move, or an unexplored frontier."""
        r, c = self.agent.row, self.agent.col
        neighbors = self._neighbors(r, c)

        # Priority 1: unvisited safe neighbor
        for nr, nc in neighbors:
            if (nr, nc) not in self.agent.visited:
                status = self.agent.cell_status.get((nr,nc), CellStatus.UNKNOWN)
                if status == CellStatus.SAFE:
                    direction = self._direction(r, c, nr, nc)
                    return self.move(direction)

        # Priority 2: backtrack to a visited cell that has unvisited safe neighbors
        for vr, vc in list(self.agent.visited):
            for nr, nc in self._neighbors(vr, vc):
                if (nr, nc) not in self.agent.visited:
                    status = self.agent.cell_status.get((nr,nc), CellStatus.UNKNOWN)
                    if status == CellStatus.SAFE:
                        path = self._bfs_path(r, c, vr, vc)
                        if path:
                            direction = self._direction(r, c, *path[0])
                            return self.move(direction)

        # Priority 3: climb out if we have gold or no safe moves left
        if self.agent.has_gold or r == 0 and c == 0:
            return self.climb()

        return self._build_state(event="STUCK")

    # ── utilities ──────────────────────────────────────────────────────────

    def _neighbors(self, r: int, c: int) -> List[Tuple[int,int]]:
        out = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                out.append((nr, nc))
        return out

    def _direction(self, r: int, c: int, nr: int, nc: int) -> str:
        if nr < r: return "UP"
        if nr > r: return "DOWN"
        if nc < c: return "LEFT"
        return "RIGHT"

    def _bfs_path(self, sr, sc, er, ec) -> List[Tuple[int,int]]:
        from collections import deque
        if (sr, sc) == (er, ec): return []
        visited = {(sr,sc)}
        queue   = deque([[(sr,sc)]])
        while queue:
            path = queue.popleft()
            r, c = path[-1]
            for nr, nc in self._neighbors(r, c):
                if (nr,nc) not in visited and (nr,nc) in self.agent.visited:
                    new_path = path + [(nr,nc)]
                    if (nr,nc) == (er,ec):
                        return new_path[1:]
                    visited.add((nr,nc))
                    queue.append(new_path)
        return []

    def _build_state(self, event: str = "", percepts: List[str] = None,
                     inference: List[Dict] = None) -> Dict:
        grid = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                status = self.agent.cell_status.get((r,c), CellStatus.UNKNOWN)
                row.append({
                    "row": r, "col": c,
                    "status": status,
                    "isAgent": (r == self.agent.row and c == self.agent.col and self.agent.alive),
                    "isGold":  (r,c) == self.world.gold and not self.agent.has_gold,
                    "isVisited": (r,c) in self.agent.visited
                })
            grid.append(row)

        return {
            "event": event,
            "grid": grid,
            "agent": {
                "row": self.agent.row,
                "col": self.agent.col,
                "hasArrow": self.agent.has_arrow,
                "hasGold": self.agent.has_gold,
                "alive": self.agent.alive,
                "score": self.agent.score,
                "visitedCount": len(self.agent.visited)
            },
            "percepts": percepts or [],
            "inference": inference or [],
            "kb": {
                "totalClauses": len(self.kb.clauses),
                "totalInferenceSteps": self.kb.total_inference_steps
            },
            "world": {
                "rows": self.rows,
                "cols": self.cols,
                "wumpusAlive": self.world.wumpus_alive
            },
            "gameOver": self.game_over,
            "won": self.won
        }

    def get_full_state(self) -> Dict:
        return self._build_state(event="QUERY")

    def reveal_world(self) -> Dict:
        """Debug/end-of-game reveal."""
        return {
            "pits":   [list(p) for p in self.world.pits],
            "wumpus": list(self.world.wumpus),
            "gold":   list(self.world.gold)
        }