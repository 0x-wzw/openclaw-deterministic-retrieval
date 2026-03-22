#!/usr/bin/env python3
"""
Unit tests for Deterministic Retrieval module.

Run with: python -m pytest test_deterministic.py -v
Or: python test_deterministic.py
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from deterministic_retrieval import (
    DeterministicRetrieval,
    RetrievalMode,
    RetrievalResult,
    EpisodicMemoryAdapter,
    retrieve,
    retrieve_memory
)


class TestRetrievalResult(unittest.TestCase):
    """Test RetrievalResult dataclass."""
    
    def test_basic_creation(self):
        """Test basic RetrievalResult creation."""
        result = RetrievalResult(
            path="/test/path",
            content="test content",
            exists=True,
            mode="deterministic"
        )
        self.assertEqual(result.path, "/test/path")
        self.assertEqual(result.content, "test content")
        self.assertTrue(result.exists)
        self.assertEqual(result.mode, "deterministic")
        self.assertEqual(result.confidence, 1.0)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = RetrievalResult(
            path="/test/path",
            content="test",
            exists=True,
            mode="deterministic",
            metadata={"key": "value"}
        )
        d = result.to_dict()
        self.assertEqual(d["path"], "/test/path")
        self.assertEqual(d["exists"], True)
        self.assertEqual(d["metadata"]["key"], "value")


class TestEpisodicMemoryAdapter(unittest.TestCase):
    """Test EpisodicMemoryAdapter."""
    
    def setUp(self):
        self.adapter = EpisodicMemoryAdapter("/tmp/test-memory")
    
    def test_get_memory_path_with_prefix(self):
        """Test resolving memory paths with prefix."""
        path = self.adapter.get_memory_path("memory/agents/halloween")
        self.assertEqual(path, Path("/tmp/test-memory/agents/halloween"))
    
    def test_get_memory_path_without_prefix(self):
        """Test resolving memory paths without prefix."""
        path = self.adapter.get_memory_path("agents/halloween")
        self.assertEqual(path, Path("/tmp/test-memory/agents/halloween"))
    
    def test_get_memory_path_absolute(self):
        """Test resolving absolute memory paths."""
        path = self.adapter.get_memory_path("/absolute/path")
        self.assertEqual(path, Path("/tmp/test-memory/absolute/path"))


class TestDeterministicRetrieval(unittest.TestCase):
    """Test DeterministicRetrieval engine."""
    
    def setUp(self):
        """Create temporary directory structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Create test files and directories
        (self.base_path / "memory").mkdir()
        (self.base_path / "memory" / "agents").mkdir()
        (self.base_path / "memory" / "agents" / "halloween").mkdir()
        
        # Create test files
        (self.base_path / "memory" / "test.txt").write_text("Hello, World!")
        (self.base_path / "memory" / "test.json").write_text(json.dumps({"key": "value"}))
        (self.base_path / "memory" / "agents" / "halloween" / "config.yaml").write_text("setting: true")
        
        self.engine = DeterministicRetrieval(
            base_path=str(self.base_path),
            mode=RetrievalMode.DETERMINISTIC
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_resolve_path_absolute(self):
        """Test resolving absolute paths."""
        path = self.engine.resolve_path("/etc/hosts")
        self.assertEqual(path, Path("/etc/hosts"))
    
    def test_resolve_path_home(self):
        """Test resolving home-relative paths."""
        path = self.engine.resolve_path("~/test")
        self.assertEqual(path, Path.home() / "test")
    
    def test_resolve_path_memory(self):
        """Test resolving memory-relative paths."""
        path = self.engine.resolve_path("memory/agents/halloween")
        expected = self.base_path / "memory" / "agents" / "halloween"
        self.assertEqual(path, expected)
    
    def test_resolve_path_relative(self):
        """Test resolving base-relative paths."""
        path = self.engine.resolve_path("memory/test.txt")
        expected = self.base_path / "memory" / "test.txt"
        self.assertEqual(path, expected)
    
    def test_retrieve_existing_file(self):
        """Test retrieving an existing file."""
        result = self.engine.retrieve("memory/test.txt")
        self.assertTrue(result.exists)
        self.assertEqual(result.content, "Hello, World!")
        self.assertEqual(result.mode, "deterministic")
    
    def test_retrieve_existing_json_file(self):
        """Test retrieving a JSON file."""
        result = self.engine.retrieve("memory/test.json")
        self.assertTrue(result.exists)
        self.assertEqual(result.content, {"key": "value"})
    
    def test_retrieve_nonexistent_file(self):
        """Test retrieving a non-existent file."""
        result = self.engine.retrieve("memory/does-not-exist.txt")
        self.assertFalse(result.exists)
        self.assertIsNone(result.content)
        self.assertIn("error", result.metadata)
    
    def test_retrieve_directory(self):
        """Test retrieving a directory."""
        result = self.engine.retrieve("memory/agents")
        self.assertTrue(result.exists)
        self.assertIsInstance(result.content, list)
        self.assertEqual(result.metadata["type"], "directory")
        
        # Should contain halloween directory
        names = [item["name"] for item in result.content]
        self.assertIn("halloween", names)
    
    def test_search_pattern(self):
        """Test searching with glob pattern."""
        results = self.engine.search("memory/*.txt")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].exists)
        self.assertEqual(results[0].content, "Hello, World!")
    
    def test_batch_retrieve(self):
        """Test batch retrieval."""
        paths = ["memory/test.txt", "memory/test.json"]
        results = self.engine.batch_retrieve(paths)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.exists for r in results))
    
    def test_mode_switching(self):
        """Test switching retrieval modes."""
        self.engine.set_mode("hybrid")
        self.assertEqual(self.engine.mode, RetrievalMode.HYBRID)
        
        self.engine.set_mode(RetrievalMode.SEMANTIC)
        self.assertEqual(self.engine.mode, RetrievalMode.SEMANTIC)
    
    def test_caching(self):
        """Test result caching."""
        # First retrieval
        result1 = self.engine.retrieve("memory/test.txt")
        self.assertTrue(result1.exists)
        
        # Should be cached
        self.assertIn("memory/test.txt:None", self.engine._cache)
        
        # Clear cache
        self.engine.clear_cache()
        self.assertEqual(len(self.engine._cache), 0)
    
    def test_hybrid_mode_retrieval(self):
        """Test hybrid mode retrieval."""
        self.engine.set_mode("hybrid")
        result = self.engine.retrieve("memory/test.txt")
        self.assertTrue(result.exists)
        self.assertEqual(result.mode, "hybrid")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_retrieve_function(self):
        """Test the retrieve() convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            result = retrieve(str(test_file), mode="deterministic")
            self.assertTrue(result.exists)
            self.assertEqual(result.content, "test content")
    
    def test_retrieve_memory_function(self):
        """Test the retrieve_memory() convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir) / "memory"
            memory_dir.mkdir()
            test_file = memory_dir / "note.md"
            test_file.write_text("memory content")
            
            # Patch the memory base path
            with patch('deterministic_retrieval.Path') as mock_path:
                result = retrieve_memory("note.md", mode="deterministic")
                # Function should add memory/ prefix if not present


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_empty_path(self):
        """Test handling of empty path - returns base_path (which exists)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeterministicRetrieval(base_path=tmpdir)
            result = engine.retrieve("")
            # Empty path resolves to base_path which is tmpdir (exists)
            self.assertTrue(result.exists)
            self.assertEqual(result.metadata["type"], "directory")
    
    def test_special_characters_in_path(self):
        """Test paths with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with special characters
            test_file = Path(tmpdir) / "file with spaces.txt"
            test_file.write_text("content")
            
            engine = DeterministicRetrieval(base_path=tmpdir)
            result = engine.retrieve("file with spaces.txt")
            self.assertTrue(result.exists)
    
    def test_nested_directories(self):
        """Test deeply nested directory retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "a" / "b" / "c" / "d"
            nested.mkdir(parents=True)
            (nested / "file.txt").write_text("deep")
            
            engine = DeterministicRetrieval(base_path=tmpdir)
            result = engine.retrieve("a/b/c/d")
            self.assertTrue(result.exists)
            self.assertEqual(result.metadata["type"], "directory")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRetrievalResult))
    suite.addTests(loader.loadTestsFromTestCase(TestEpisodicMemoryAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestDeterministicRetrieval))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
