# mdproc Docker Container

A multi-architecture Docker container for the mdproc markdown processor, following the compiler container pattern (like gcc/clang containers).

## Quick Start

```bash
# Recommended alias (like compiler containers)
alias mdproc='docker run --rm -v $(pwd):/workspace dawsonlp/mdproc'

# Use like a local CLI
mdproc convert -i document.md -f pdf
mdproc formats
mdproc --version
```

## Usage Patterns

### 1. Direct Usage (Compiler Pattern)

```bash
# Convert markdown to PDF
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i document.md -f pdf

# Convert with custom options
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i doc.md -f pdf --title "My Document" --author "John Doe"

# Convert to different formats
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i README.md -f html
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i notes.md -f docx
```

### 2. Batch Processing

```bash
# Process multiple files
for file in *.md; do
    docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i "$file" -f pdf
done

# Or with find
find . -name "*.md" -exec docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i {} -f pdf \;
```

### 3. CI/CD Integration

```yaml
# GitHub Actions example
- name: Convert documentation to PDF
  run: |
    docker run --rm -v $PWD:/workspace dawsonlp/mdproc convert -i README.md -f pdf -o dist/README.pdf
```

```bash
# Makefile integration
%.pdf: %.md
	docker run --rm -v $(PWD):/workspace dawsonlp/mdproc convert -i $< -f pdf -o $@

docs: $(patsubst %.md,%.pdf,$(wildcard *.md))
```

### 4. Development Workflow

```bash
# Create alias in your shell profile (.bashrc, .zshrc, etc.)
echo "alias mdproc='docker run --rm -v \$(pwd):/workspace dawsonlp/mdproc'" >> ~/.bashrc

# Then use normally
mdproc convert -i document.md -f pdf
mdproc validate -i document.md
mdproc formats
```

## Container Details

### Architecture Support
- **linux/amd64** - Intel/AMD 64-bit
- **linux/arm64** - ARM 64-bit (Apple Silicon, ARM servers)

### Base Image
- **Ubuntu 25.04** - Tested and verified platform
- **Python 3.13** - Latest Python with all dependencies
- **WeasyPrint** - High-quality PDF generation
- **Fonts** - Liberation, DejaVu, Noto for proper rendering

### Volume Conventions
- `/workspace` - Main working directory (mount your project here)
- Container runs as current user (no permission issues)
- Output files created in mounted directory

### Security
- Runs as non-root user
- No network access required for basic operations
- Stateless execution (no persistent data in container)

## Available Commands

```bash
# Show help
docker run --rm dawsonlp/mdproc --help

# List supported formats
docker run --rm dawsonlp/mdproc formats

# Show version
docker run --rm dawsonlp/mdproc --version

# Convert documents
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i input.md -f FORMAT

# Validate markdown
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc validate -i input.md

# Show examples
docker run --rm dawsonlp/mdproc example
```

## Supported Formats

| Input | Output Formats |
|-------|----------------|
| Markdown | PDF, HTML, DOCX, TXT |

### Format Details
- **PDF** - High-quality, printable documents (WeasyPrint/ReportLab)
- **HTML** - Web-ready documents with CSS styling
- **DOCX** - Microsoft Word compatible documents
- **TXT** - Clean plain text output

## Examples

### Basic Conversion
```bash
# Create a test document
echo "# Hello Docker\n\nThis is a **test** document." > test.md

# Convert to PDF
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i test.md -f pdf

# Result: test.pdf created in current directory
```

### Advanced Usage
```bash
# Convert with metadata
docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert \
    -i document.md \
    -f pdf \
    --title "Project Documentation" \
    --author "Development Team" \
    --subject "Technical Specification"

# Convert to multiple formats
for format in pdf html docx txt; do
    docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i README.md -f $format
done
```

### Project Integration
```bash
# Add to package.json scripts
{
  "scripts": {
    "docs:pdf": "docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i README.md -f pdf -o docs/README.pdf",
    "docs:html": "docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i README.md -f html -o docs/README.html"
  }
}

# Add to Makefile
docs:
	docker run --rm -v $(PWD):/workspace dawsonlp/mdproc convert -i README.md -f pdf -o dist/README.pdf
	docker run --rm -v $(PWD):/workspace dawsonlp/mdproc convert -i CHANGELOG.md -f pdf -o dist/CHANGELOG.pdf
```

## Troubleshooting

### Permission Issues
If you encounter permission issues with output files:
```bash
# Check current user ID
id -u

# The container runs as the same user, so this shouldn't happen
# If it does, ensure the output directory is writable
chmod 755 $(pwd)
```

### Font Issues
The container includes common fonts, but for special characters:
```bash
# Check available fonts in container
docker run --rm dawsonlp/mdproc sh -c "fc-list | head -10"
```

### Large Files
For very large markdown files:
```bash
# Increase Docker memory if needed
docker run --rm -m 2g -v $(pwd):/workspace dawsonlp/mdproc convert -i large-file.md -f pdf
```

## Building Locally

```bash
# Clone and build
git clone <repository>
cd servers/document-processor

# Build for local testing
docker build -t mdproc-local .

# Test local build
docker run --rm -v $(pwd):/workspace mdproc-local convert -i test.md -f pdf
```

## Registry Information

- **Registry**: `dawsonlp/mdproc`
- **Tags**: `latest`, `1.0.0`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Size**: ~500MB (includes all dependencies)

## Support

For issues, feature requests, or contributions, please visit the project repository.
