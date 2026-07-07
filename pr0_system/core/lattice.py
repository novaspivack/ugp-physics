"""
Lattice and Graph Structures for PR-0

Provides abstract lattice/graph substrate for field evolution.

Author: AI Assistant
Date: October 31, 2025
Session: 25.10
Reference: SESSION_25_9_PR0_COMPLETE_TECHNICAL_SPECIFICATION.md
"""

import numpy as np
from typing import Tuple, List, Optional


class Lattice:
    """
    Abstract lattice structure supporting multiple boundary conditions.
    
    Supports:
    - Square lattice (2D)
    - Hexagonal lattice (2D) [future]
    - Arbitrary graph [future]
    - Boundary modes: torus, open, cylinder_x, cylinder_y
    """
    
    _ALLOWED_BOUNDARIES = {"torus", "open", "cylinder_x", "cylinder_y"}
    
    def __init__(
        self,
        L_x: int,
        L_y: int,
        lattice_type: str = "square",
        periodic: bool = True,
        boundary: str | None = None,
    ):
        """
        Initialize lattice.
        
        Args:
            L_x: Grid width
            L_y: Grid height
            lattice_type: 'square', 'hexagonal', or 'graph'
            periodic: Backward-compatible flag for full periodicity (torus)
            boundary: Optional boundary mode ('torus', 'open', 'cylinder_x', 'cylinder_y')
        """
        self.L_x = L_x
        self.L_y = L_y
        self.lattice_type = lattice_type

        if lattice_type not in ["square", "hexagonal", "graph"]:
            raise ValueError(f"Unknown lattice type: {lattice_type}")

        if boundary is None:
            self.boundary = "torus" if periodic else "open"
        else:
            self.boundary = str(boundary).lower()
        if self.boundary not in self._ALLOWED_BOUNDARIES:
            raise ValueError(f"Unknown boundary mode: {self.boundary}")

        # Backward-compatibility flag (True only for full torus)
        self.periodic = self.boundary == "torus"
        self.periodic_x = self.boundary in {"torus", "cylinder_x"}
        self.periodic_y = self.boundary in {"torus", "cylinder_y"}

        self.N_vertices = L_x * L_y
    
    def neighbors(self, i: int, j: int) -> List[Tuple[int, int]]:
        """
        Get neighbors of vertex (i, j).
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            List of (row, col) tuples for neighbors
        """
        if self.lattice_type == 'square':
            return self._square_neighbors(i, j)
        elif self.lattice_type == 'hexagonal':
            return self._hex_neighbors(i, j)
        else:
            raise NotImplementedError(f"Neighbors not implemented for {self.lattice_type}")
    
    def _square_neighbors(self, i: int, j: int) -> List[Tuple[int, int]]:
        """4-neighbors for square lattice."""
        neighbors: List[Tuple[int, int]] = []
        if self.periodic_y or i > 0:
            im = (i - 1) % self.L_y if self.periodic_y else i - 1
            neighbors.append((im, j))
        if self.periodic_y or i < self.L_y - 1:
            ip = (i + 1) % self.L_y if self.periodic_y else i + 1
            neighbors.append((ip, j))
        if self.periodic_x or j > 0:
            jm = (j - 1) % self.L_x if self.periodic_x else j - 1
            neighbors.append((i, jm))
        if self.periodic_x or j < self.L_x - 1:
            jp = (j + 1) % self.L_x if self.periodic_x else j + 1
            neighbors.append((i, jp))
        return neighbors
    
    def _hex_neighbors(self, i: int, j: int) -> List[Tuple[int, int]]:
        """6-neighbors for hexagonal lattice."""
        # Even/odd rows have different neighbor patterns
        if i % 2 == 0:
            offsets = [(-1, 0), (-1, -1), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:
            offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        
        neighbors = []
        for di, dj in offsets:
            ni, nj = i + di, j + dj
            
            if self.periodic:
                ni = ni % self.L_y
                nj = nj % self.L_x
                neighbors.append((ni, nj))
            else:
                if 0 <= ni < self.L_y and 0 <= nj < self.L_x:
                    neighbors.append((ni, nj))
        
        return neighbors
    
    def distance(self, i1: int, j1: int, i2: int, j2: int) -> float:
        """
        Compute distance between two vertices.
        
        Accounts for periodic boundary conditions if enabled.
        """
        dx = j2 - j1
        dy = i2 - i1
        if self.periodic_x:
            if abs(dx) > self.L_x / 2:
                dx -= np.sign(dx) * self.L_x
        if self.periodic_y:
            if abs(dy) > self.L_y / 2:
                dy -= np.sign(dy) * self.L_y
        return np.sqrt(dx**2 + dy**2)
    
    def laplacian(self, field: np.ndarray) -> np.ndarray:
        """
        Compute discrete Laplacian of field.
        
        Uses 5-point stencil for square lattice:
        ∇²ψ ≈ (ψ_{i+1,j} + ψ_{i-1,j} + ψ_{i,j+1} + ψ_{i,j-1} - 4ψ_{i,j})
        
        Args:
            field: 2D array (L_y × L_x)
            
        Returns:
            Laplacian field (same shape)
        """
        if self.lattice_type == 'square':
            lap = (
                np.roll(field, 1, axis=0)
                + np.roll(field, -1, axis=0)
                + np.roll(field, 1, axis=1)
                + np.roll(field, -1, axis=1)
                - 4 * field
            )

            if not self.periodic_y:
                top_wrap = np.roll(field, 1, axis=0)[0, :]
                bottom_wrap = np.roll(field, -1, axis=0)[-1, :]
                lap[0, :] -= top_wrap
                lap[-1, :] -= bottom_wrap
            if not self.periodic_x:
                left_wrap = np.roll(field, 1, axis=1)[:, 0]
                right_wrap = np.roll(field, -1, axis=1)[:, -1]
                lap[:, 0] -= left_wrap
                lap[:, -1] -= right_wrap
            return lap
        else:
            raise NotImplementedError(f"Laplacian not implemented for {self.lattice_type}")
    
    def __repr__(self):
        return (
            f"Lattice({self.L_x}×{self.L_y}, type={self.lattice_type}, "
            f"boundary={self.boundary})"
        )


class DynamicGraph:
    """
    Dynamic graph with topology changes (Pachner moves).
    
    For future PR-0 v2.0 with full GR.
    """
    
    def __init__(self):
        self.vertices = set()
        self.edges = set()
        self.faces = set()
        self.move_history = []
    
    def pachner_1_3(self, face):
        """Split triangle into 3 triangles (2D)."""
        raise NotImplementedError("Dynamic topology not yet implemented")
    
    def pachner_2_2(self, edge):
        """Flip edge (2D)."""
        raise NotImplementedError("Dynamic topology not yet implemented")
    
    def curvature(self, vertex):
        """Compute discrete curvature (deficit angle)."""
        raise NotImplementedError("Curvature not yet implemented")

