#!/usr/bin/env python3
"""
Command-line interface for OpenClaw Deterministic Retrieval.

Usage:
    openclaw-retrieve --mode deterministic --path memory/agents/halloween
    openclaw-retrieve --mode hybrid --path memory/2026-03-22.md
    openclaw-retrieve --mode semantic --path "*.jsonl" --search
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from deterministic_retrieval import (
    DeterministicRetrieval,
    RetrievalMode,
    RetrievalResult
)


def format_output(result: RetrievalResult, output_format: str = "auto") -> str:
    """Format retrieval result for output."""
    if output_format == "json":
        return json.dumps(result.to_dict(), indent=2, default=str)
    
    if not result.exists:
        return f"[NOT FOUND] {result.path}\n  Error: {result.metadata.get('error', 'Unknown error')}"
    
    lines = [
        f"[FOUND] {result.path}",
        f"  Mode: {result.mode}",
        f"  Confidence: {result.confidence}",
    ]
    
    if "type" in result.metadata:
        lines.append(f"  Type: {result.metadata['type']}")
    
    if "size" in result.metadata:
        lines.append(f"  Size: {result.metadata['size']} bytes")
    
    if "item_count" in result.metadata:
        lines.append(f"  Items: {result.metadata['item_count']}")
    
    lines.append("" + "=" * 50)
    
    # Content preview
    if isinstance(result.content, list):
        lines.append(f"Directory contents ({len(result.content)} items):")
        for item in result.content[:20]:  # Limit to first 20
            type_icon = "📁" if item.get("type") == "directory" else "📄"
            lines.append(f"  {type_icon} {item['name']}")
        if len(result.content) > 20:
            lines.append(f"  ... and {len(result.content) - 20} more items")
    elif isinstance(result.content, dict):
        lines.append("JSON content:")
        lines.append(json.dumps(result.content, indent=2)[:1000])
    elif isinstance(result.content, str):
        # Truncate long text
        preview = result.content[:2000]
        if len(result.content) > 2000:
            preview += f"\n... ({len(result.content) - 2000} more characters)"
        lines.append(preview)
    else:
        lines.append(f"Binary content: {type(result.content)}")
    
    return "\n".join(lines)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="openclaw-retrieve",
        description="Deterministic retrieval for OpenClaw - predictable and debuggable file/memory retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Retrieve a specific file
  openclaw-retrieve --mode deterministic --path memory/2026-03-22.md

  # List directory contents
  openclaw-retrieve --mode deterministic --path memory/agents

  # Search with pattern
  openclaw-retrieve --mode hybrid --search --path "memory/*.md"

  # JSON output for piping
  openclaw-retrieve --mode deterministic --path memory/agents --format json

Modes:
  deterministic  Exact path-based lookup (default)
  semantic       Semantic similarity search (requires embeddings)
  hybrid         Path lookup with semantic enhancement
        """
    )
    
    parser.add_argument(
        "--path", "-p",
        required=True,
        help="Path to retrieve (file, directory, or glob pattern)"
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["deterministic", "semantic", "hybrid"],
        default="deterministic",
        help="Retrieval mode (default: deterministic)"
    )
    
    parser.add_argument(
        "--base-path", "-b",
        default="~/.openclaw/workspace",
        help="Base path for relative lookups (default: ~/.openclaw/workspace)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["auto", "json", "raw"],
        default="auto",
        help="Output format (default: auto)"
    )
    
    parser.add_argument(
        "--search", "-s",
        action="store_true",
        help="Treat path as glob pattern for search"
    )
    
    parser.add_argument(
        "--content-type", "-t",
        choices=["text", "json", "auto"],
        default="auto",
        help="Content type hint for parsing"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable result caching"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Validate content type
    content_type = None if args.content_type == "auto" else args.content_type
    
    try:
        # Initialize retrieval engine
        engine = DeterministicRetrieval(
            base_path=args.base_path,
            mode=RetrievalMode(args.mode),
            enable_caching=not args.no_cache
        )
        
        # Execute retrieval
        if args.search:
            results = engine.search(args.path)
            
            if args.format == "json":
                output = json.dumps([r.to_dict() for r in results], indent=2, default=str)
                print(output)
            else:
                for result in results:
                    print(format_output(result, args.format))
                    print()
            
            return 0 if results else 1
        else:
            result = engine.retrieve(args.path, content_type)
            
            if args.format == "raw":
                if result.exists:
                    if isinstance(result.content, (dict, list)):
                        print(json.dumps(result.content, indent=2))
                    else:
                        print(result.content)
                else:
                    print(f"Error: {result.metadata.get('error', 'Not found')}", file=sys.stderr)
                    return 1
            else:
                print(format_output(result, args.format))
            
            return 0 if result.exists else 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())