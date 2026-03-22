#!/usr/bin/env python3
"""
Deterministic Retrieval Module for OpenClaw

Provides predictable, path-based file and memory retrieval with optional
semantic overlay support for hybrid mode.

Modes:
- deterministic: Exact path-based lookup only
- semantic: Semantic similarity search (placeholder for integration)
- hybrid: Path-based lookup with semantic fallback/enhancement
"""

import os
import json
import glob
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum


class RetrievalMode(Enum):
    """Supported retrieval modes."""
    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class RetrievalResult:
    """Result container for retrieval operations."""
    path: str
    content: Any
    exists: bool
    mode: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "exists": self.exists,
            "mode": self.mode,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class EpisodicMemoryAdapter:
    """
    Adapter for episodic-memory skill integration.
    Provides interface to OpenClaw's memory system.
    """
    
    DEFAULT_MEMORY_PATH = "~/.openclaw/workspace/memory"
    
    def __init__(self, memory_base_path: Optional[str] = None):
        if memory_base_path is None:
            memory_base_path = self.DEFAULT_MEMORY_PATH
        self.memory_base = Path(memory_base_path).expanduser()
        self.agent_comm_logs = self.memory_base / "agent-comm-logs"
        
    def get_memory_path(self, relative_path: str) -> Path:
        """Resolve a memory-relative path to absolute path."""
        # Handle paths like "memory/agents/halloween" or "agents/halloween"
        clean_path = relative_path.lstrip("/")
        if clean_path.startswith("memory/"):
            clean_path = clean_path[7:]  # Remove 'memory/' prefix
        return self.memory_base / clean_path
    
    def list_daily_notes(self) -> List[Path]:
        """List all daily memory notes."""
        pattern = self.memory_base / "*.md"
        return sorted(glob.glob(str(pattern)))
    
    def get_comm_logs(self, date: Optional[str] = None) -> List[Path]:
        """Get agent communication logs for a specific date."""
        if date:
            log_file = self.agent_comm_logs / f"{date}.jsonl"
            return [log_file] if log_file.exists() else []
        # Return all logs
        return sorted(glob.glob(str(self.agent_comm_logs / "*.jsonl")))


class DeterministicRetrieval:
    """
    Core deterministic retrieval engine.
    
    Provides predictable, debuggable path-based lookups with optional
    semantic search overlay for enhanced retrieval capabilities.
    """
    
    def __init__(
        self,
        base_path: str = "~/.openclaw/workspace",
        mode: RetrievalMode = RetrievalMode.DETERMINISTIC,
        enable_caching: bool = True
    ):
        self.base_path = Path(base_path).expanduser()
        self.mode = mode
        self.enable_caching = enable_caching
        self._cache: Dict[str, RetrievalResult] = {}
        self.memory_adapter = EpisodicMemoryAdapter(str(self.base_path / "memory"))
        
    def set_mode(self, mode: Union[str, RetrievalMode]) -> None:
        """Switch retrieval mode."""
        if isinstance(mode, str):
            self.mode = RetrievalMode(mode.lower())
        else:
            self.mode = mode
            
    def resolve_path(self, query: str) -> Path:
        """
        Resolve a query path to absolute path.
        
        Supports:
        - Absolute paths: /home/user/file.txt
        - Home-relative: ~/file.txt
        - Memory-relative: memory/agents/halloween
        - Workspace-relative: agents/halloween
        """
        # Handle empty query
        if not query:
            return self.base_path
            
        # Handle special prefixes
        if query.startswith("memory/"):
            return self.memory_adapter.get_memory_path(query)
        elif query.startswith("~/"):
            return Path(query).expanduser()
        elif query.startswith("/"):
            return Path(query)
        else:
            # Relative to base path
            return self.base_path / query
    
    def retrieve(
        self,
        path: str,
        content_type: Optional[str] = None
    ) -> RetrievalResult:
        """
        Retrieve content from a path.
        
        Args:
            path: The path to retrieve (file or directory)
            content_type: Optional content type hint ('text', 'json', 'list')
            
        Returns:
            RetrievalResult with content and metadata
        """
        # Check cache in deterministic mode
        cache_key = f"{path}:{content_type}"
        if self.enable_caching and self.mode == RetrievalMode.DETERMINISTIC:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Resolve path
        resolved = self.resolve_path(path)
        
        # Execute retrieval based on mode
        if self.mode == RetrievalMode.DETERMINISTIC:
            result = self._deterministic_retrieve(resolved, content_type)
        elif self.mode == RetrievalMode.SEMANTIC:
            result = self._semantic_retrieve(resolved, content_type)
        else:  # HYBRID
            result = self._hybrid_retrieve(resolved, content_type)
        
        # Cache if enabled
        if self.enable_caching:
            self._cache[cache_key] = result
            
        return result
    
    def _deterministic_retrieve(
        self,
        resolved_path: Path,
        content_type: Optional[str]
    ) -> RetrievalResult:
        """
        Pure deterministic retrieval - exact path lookup only.
        """
        path_str = str(resolved_path)
        
        if not resolved_path.exists():
            return RetrievalResult(
                path=path_str,
                content=None,
                exists=False,
                mode="deterministic",
                confidence=1.0,
                metadata={"error": "Path does not exist"}
            )
        
        # Handle directory
        if resolved_path.is_dir():
            contents = self._list_directory(resolved_path)
            return RetrievalResult(
                path=path_str,
                content=contents,
                exists=True,
                mode="deterministic",
                confidence=1.0,
                metadata={"type": "directory", "item_count": len(contents)}
            )
        
        # Handle file
        content = self._read_file(resolved_path, content_type)
        return RetrievalResult(
            path=path_str,
            content=content,
            exists=True,
            mode="deterministic",
            confidence=1.0,
            metadata={
                "type": "file",
                "size": resolved_path.stat().st_size,
                "content_type": content_type or "auto"
            }
        )
    
    def _semantic_retrieve(
        self,
        resolved_path: Path,
        content_type: Optional[str]
    ) -> RetrievalResult:
        """
        Semantic retrieval - placeholder for semantic search integration.
        """
        # For now, falls back to deterministic with warning
        result = self._deterministic_retrieve(resolved_path, content_type)
        result.mode = "semantic"
        result.metadata["note"] = "Semantic search requires external embedding service"
        return result
    
    def _hybrid_retrieve(
        self,
        resolved_path: Path,
        content_type: Optional[str]
    ) -> RetrievalResult:
        """
        Hybrid retrieval - deterministic first, semantic enhancement.
        """
        # Start with deterministic
        result = self._deterministic_retrieve(resolved_path, content_type)
        
        # Add semantic metadata if content exists
        if result.exists and isinstance(result.content, str):
            # Could add semantic analysis here
            result.metadata["semantic_available"] = True
            
        result.mode = "hybrid"
        return result
    
    def _list_directory(self, path: Path) -> List[Dict[str, Any]]:
        """List directory contents with metadata."""
        items = []
        for item in sorted(path.iterdir()):
            item_info = {
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
            }
            if item.is_file():
                stat = item.stat()
                item_info["size"] = stat.st_size
                item_info["modified"] = stat.st_mtime
            items.append(item_info)
        return items
    
    def _read_file(
        self,
        path: Path,
        content_type: Optional[str]
    ) -> Union[str, Dict, List, bytes]:
        """Read file content with type detection."""
        # Determine content type
        if content_type is None:
            if path.suffix == ".json":
                content_type = "json"
            elif path.suffix in [".md", ".txt", ".py", ".js", ".yml", ".yaml"]:
                content_type = "text"
            else:
                content_type = "text"
        
        # Read based on type
        if content_type == "json":
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif content_type == "text":
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            with open(path, 'rb') as f:
                return f.read()
    
    def batch_retrieve(
        self,
        paths: List[str],
        content_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Retrieve multiple paths."""
        return [self.retrieve(p, content_type) for p in paths]
    
    def search(
        self,
        pattern: str,
        base_path: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Search for files matching a glob pattern.
        Deterministic pattern matching only.
        """
        search_base = self.base_path if base_path is None else Path(base_path)
        matches = glob.glob(str(search_base / pattern), recursive=True)
        
        results = []
        for match in matches:
            result = self._deterministic_retrieve(Path(match), None)
            results.append(result)
        
        return results
    
    def clear_cache(self) -> None:
        """Clear the retrieval cache."""
        self._cache.clear()


# Convenience functions for quick access
def retrieve(
    path: str,
    mode: str = "deterministic",
    base_path: str = "~/.openclaw/workspace"
) -> RetrievalResult:
    """Quick retrieval function."""
    engine = DeterministicRetrieval(
        base_path=base_path,
        mode=RetrievalMode(mode)
    )
    return engine.retrieve(path)


def retrieve_memory(path: str, mode: str = "deterministic") -> RetrievalResult:
    """Quick retrieval from memory directory."""
    if not path.startswith("memory/"):
        path = f"memory/{path}"
    return retrieve(path, mode, "~/.openclaw/workspace")