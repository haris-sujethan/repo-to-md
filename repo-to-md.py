import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


EXTENSIONS = {
    ".xml", ".xsl", ".xslt", ".wsdl", ".raml",
    ".dwl", ".dw",
    ".properties", ".yaml", ".yml", ".toml", ".env",
    ".json", ".graphql", ".proto", ".avsc", ".csv",
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".pyi",
    ".java", ".kt", ".kts", ".groovy", ".scala",
    ".cs", ".fs", ".vb",
    ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".sh", ".bash", ".zsh", ".ps1", ".bat",
    ".gradle", ".tf", ".hcl",
    ".md", ".txt", ".rst",
    ".dockerfile", "dockerfile", ".dockerignore",
    ".gitignore", ".editorconfig", ".nvmrc",
    ".ini", ".cfg", ".conf",
    ".sql",
}

SKIP_DIRS = {
    ".git", ".svn", ".hg",
    "target", "build", "dist", "out", ".output", "bin", "obj",
    "node_modules", ".venv", "venv", "env", "__pycache__",
    ".gradle", ".m2", "vendor", "packages",
    ".idea", ".vscode", "__macosx", ".ds_store",
    "coverage", ".nyc_output",
    ".cache", "tmp", "temp", "logs",
}

LANG_MAP = {
    ".xml": "xml", ".xsl": "xml", ".xslt": "xml", ".wsdl": "xml",
    ".raml": "yaml",
    ".dwl": "dataweave", ".dw": "dataweave",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".json": "json", ".env": "properties",
    ".properties": "properties", ".ini": "ini", ".cfg": "ini", ".conf": "nginx",
    ".graphql": "graphql", ".proto": "protobuf", ".avsc": "json", ".csv": "csv",
    ".sql": "sql",
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss", ".sass": "sass", ".less": "less",
    ".js": "javascript", ".jsx": "jsx", ".ts": "typescript", ".tsx": "tsx",
    ".mjs": "javascript", ".cjs": "javascript",
    ".py": "python", ".pyi": "python",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".groovy": "groovy", ".scala": "scala",
    ".cs": "csharp", ".fs": "fsharp", ".vb": "vb",
    ".go": "go", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
    ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".ps1": "powershell", ".bat": "batch",
    ".gradle": "groovy", ".tf": "hcl", ".hcl": "hcl",
    ".dockerfile": "dockerfile", "dockerfile": "dockerfile",
    ".gitignore": "gitignore", ".dockerignore": "gitignore",
    ".editorconfig": "ini", ".nvmrc": "",
    ".md": "markdown", ".rst": "rst", ".txt": "",
}


def normalise(path, root):
    rel = path.relative_to(root).as_posix()
    prefix = root.name + "/"
    if rel.startswith(prefix):
        rel = rel[len(prefix):]
    return rel


def should_skip_dir(name, extra_skip):
    n = name.lower()
    return n in SKIP_DIRS or n in extra_skip


def get_lang(path):
    suffix = path.suffix.lower()
    if not suffix:
        return LANG_MAP.get(path.name.lower(), "")
    return LANG_MAP.get(suffix, suffix.lstrip("."))


def is_binary(path, sample=8192):
    try:
        return b"\x00" in path.read_bytes()[:sample]
    except Exception:
        return False


def collect_files(root, allowed_ext, extra_skip):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in sorted(dirnames)
            if not should_skip_dir(d, extra_skip)
        ]
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            ext = p.suffix.lower()
            if ext in allowed_ext or p.name.lower() in allowed_ext:
                files.append(p)
    return files


def build_tree(files, root):
    lines = [f"## {root.name}/\n"]
    for f in files:
        rel = normalise(f, root)
        depth = len(Path(rel).parts) - 1
        indent = "  " * depth
        lines.append(f"{indent}- `{rel}`")
    return "\n".join(lines)


def file_to_block(path, root, max_lines, include_empty):
    rel = normalise(path, root)
    lang = get_lang(path)

    if is_binary(path):
        return f"## `{rel}`\n\n> Skipped: binary file\n"

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"## `{rel}`\n\n> Could not read file: {e}\n"

    if not raw.strip() and not include_empty:
        return None

    lines = raw.splitlines()
    if len(lines) > max_lines:
        return (
            f"## `{rel}`\n\n"
            f"> Skipped: {len(lines)} lines exceeds --max-lines {max_lines}\n"
        )

    clean = "\n".join(line.rstrip() for line in lines)
    lang_tag = f" {lang}" if lang else ""

    return f"## `{rel}`\n\n```{lang_tag}\n{clean}\n```\n"


def convert(repo_path, output, extensions, extra_skip, max_lines, include_empty, no_summary):
    root = Path(os.path.abspath(repo_path))

    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    allowed_ext = extensions or EXTENSIONS
    files = collect_files(root, allowed_ext, extra_skip)

    if not files:
        print("warning: no matching files found. Check --extensions or --exclude.", file=sys.stderr)

    out_path = Path(output) if output else Path(f"{root.name}.md")

    sections = []

    sections.append(
        f"# {root.name}\n\n"
        f"Generated by repo-to-md on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  \n"
        f"Source: `{root}`  \n"
        f"Files included: {len(files)}\n"
    )

    if not no_summary:
        sections.append(build_tree(files, root))
        sections.append("---\n")

    skipped = 0
    for f in files:
        block = file_to_block(f, root, max_lines, include_empty)
        if block is None:
            skipped += 1
        else:
            sections.append(block)

    out_path.write_text("\n\n".join(sections), encoding="utf-8")

    included = len(files) - skipped
    print(f"done: {included} file(s) written to {out_path}")
    if skipped:
        print(f"      {skipped} empty file(s) skipped (use --include-empty to keep)")


def parse_args():
    p = argparse.ArgumentParser(
        description="Convert a repository into a single Markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("repo", help="Path to the repository root")
    p.add_argument("-o", "--output", help="Output file path")
    p.add_argument("-e", "--extensions", help='Extensions to include, e.g. ".xml,.py,.yaml"')
    p.add_argument("-x", "--exclude", help='Directories to skip, e.g. "docs,scratch"')
    p.add_argument("--max-lines", type=int, default=1000, help="Skip files over N lines (default: 1000)")
    p.add_argument("--include-empty", action="store_true", help="Include empty files")
    p.add_argument("--no-summary", action="store_true", help="Omit the file tree")
    return p.parse_args()


def main():
    args = parse_args()

    extensions = None
    if args.extensions:
        extensions = set()
        for e in args.extensions.split(","):
            e = e.strip()
            if e:
                extensions.add(e if e.startswith(".") else f".{e}")

    extra_skip = set()
    if args.exclude:
        extra_skip = {d.strip().lower() for d in args.exclude.split(",") if d.strip()}

    convert(
        repo_path=args.repo,
        output=args.output,
        extensions=extensions,
        extra_skip=extra_skip,
        max_lines=args.max_lines,
        include_empty=args.include_empty,
        no_summary=args.no_summary,
    )


if __name__ == "__main__":
    main()