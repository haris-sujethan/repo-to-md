## repo-to-md
Convert your repository into a single Markdown file for LLM context. 

Plain text / Markdown outperform PDFs for LLM use (less token overhead, cleaner parsing, better retrieval, etc.)

- **No external libraries** — Python standard library, nothing to install
- **Safe for enterprise** — no network calls, runs completely offline

## How to use
```bash
python repo-to-md.py <repo_dir>
```

The script generates a `<repo_name>.md` file in the current directory.

#### Custom output path:
```bash
python repo-to-md.py <repo_dir> -o output.md
```

#### Only include specific file types:
```bash
python repo-to-md.py <repo_dir> -e ".xml,.dwl,.yaml,.properties"
```

#### Skip additional directories:
```bash
python repo-to-md.py <repo_dir> -x "docs,scratch,archive"
```

#### Skip large generated files:
```bash
python repo-to-md.py <repo_dir> --max-lines 300
```

#### Include empty files (skipped by default):
```bash
python repo-to-md.py <repo_dir> --include-empty
```

## Output format
Each file is written as a fenced code block with the correct language tag:

    ## `src/main/mule/my-flow.xml`

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <mule ...>
    ```

A file tree summary is included at the top so the LLM understands the project structure before reading code.