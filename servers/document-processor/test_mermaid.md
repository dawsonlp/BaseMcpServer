# Mermaid Diagram Test

This document tests Mermaid diagram support in our markdown processor.

## Flowchart Example

```mermaid
flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Converter
    participant Mermaid
    
    User->>CLI: mdproc convert
    CLI->>Converter: process document
    Converter->>Mermaid: generate diagrams
    Mermaid-->>Converter: return images
    Converter-->>CLI: converted document
    CLI-->>User: success
```

## Class Diagram

```mermaid
classDiagram
    class DocumentConverter {
        +source_format: DocumentFormat
        +target_format: DocumentFormat
        +convert(document, options): ConversionResult
    }
    
    class MarkdownToPdfConverter {
        +convert(document, options): ConversionResult
        -_markdown_to_html(): str
        -_html_to_pdf(): None
    }
    
    class MermaidProcessor {
        +process_markdown(): str
        -_generate_diagram(): None
    }
    
    DocumentConverter <|-- MarkdownToPdfConverter
    MarkdownToPdfConverter --> MermaidProcessor
```

## Architecture Overview

This demonstrates how our hexagonal architecture handles Mermaid diagrams:

```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI[CLI Interface]
    end
    
    subgraph "Application Layer"
        UC[Use Cases]
        SVC[Services]
    end
    
    subgraph "Domain Layer"
        DOC[Document]
        CONV[Converters]
        FMT[Formats]
    end
    
    subgraph "Infrastructure Layer"
        PDF[PDF Engine]
        HTML[HTML Engine]
        MERM[Mermaid Processor]
    end
    
    CLI --> UC
    UC --> SVC
    SVC --> CONV
    CONV --> PDF
    CONV --> HTML
    CONV --> MERM
    
    CONV --> DOC
    CONV --> FMT
```

## Summary

The Mermaid integration allows us to:

1. **Process diagrams** automatically during conversion
2. **Support multiple formats** (PNG for PDF, SVG for HTML)
3. **Maintain clean architecture** with proper separation of concerns
4. **Provide fallback handling** when diagram generation fails

This enhances our document processor significantly for technical documentation!
