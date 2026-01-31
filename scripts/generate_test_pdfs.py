"""
Generate Test PDFs for RAG Bot

Creates sample AI Bootcamp PDF documents for testing the RAG pipeline.
Run: python scripts/generate_test_pdfs.py
"""

import os
from fpdf import FPDF

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def create_pdf(filename: str, title: str, content_sections: list):
    """Create a simple PDF with the given content."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add a page
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    # Content
    pdf.set_font("Helvetica", "", 11)
    
    for section in content_sections:
        if section.startswith("##"):
            # Section header
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(5)
            pdf.cell(0, 8, section.replace("## ", ""), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
        elif section.startswith("- "):
            # Bullet point
            pdf.set_x(20)
            pdf.multi_cell(0, 6, section)
        else:
            # Normal paragraph
            pdf.multi_cell(0, 6, section)
            pdf.ln(3)
    
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    filepath = os.path.join(DATA_DIR, filename)
    pdf.output(filepath)
    print(f"Created: {filepath}")


def main():
    print("Generating test PDFs for RAG Bot...")
    
    # 1. AI Bootcamp FAQ
    create_pdf(
        "ai_bootcamp_faq.pdf",
        "AI Bootcamp - Frequently Asked Questions",
        [
            "## What is the AI Bootcamp?",
            "The AI Bootcamp is a comprehensive 12-week training program designed to teach participants the fundamentals of artificial intelligence, machine learning, and practical applications using modern tools and frameworks.",
            
            "## What are the prerequisites?",
            "- Basic programming knowledge (preferably Python)",
            "- Understanding of mathematics (linear algebra, statistics)",
            "- Familiarity with command line tools",
            "- A computer with at least 8GB RAM",
            
            "## How long is the program?",
            "The standard bootcamp runs for 12 weeks, with approximately 10-15 hours of commitment per week including lectures, labs, and projects.",
            
            "## What topics are covered?",
            "- Week 1-3: Python fundamentals and data manipulation",
            "- Week 4-6: Machine learning basics with scikit-learn",
            "- Week 7-9: Deep learning with PyTorch/TensorFlow",
            "- Week 10-12: NLP, RAG systems, and deployment",
            
            "## What tools will we use?",
            "Python 3.10+, Jupyter notebooks, VS Code, Git, Azure AI services, MongoDB Atlas, Discord for collaboration, and GitHub for version control.",
            
            "## How do I get support?",
            "Use the Discord bot (!ask command), attend office hours on Wednesdays, or post in the discussion forums. Instructors typically respond within 24 hours.",
            
            "## Is there a certificate?",
            "Yes, participants who complete all projects and pass the final assessment receive a certificate of completion from the AI Engineering Institute.",
        ]
    )
    
    # 2. Training Notes Week 1
    create_pdf(
        "training_week1_intro_to_ai.pdf",
        "Week 1: Introduction to AI Engineering",
        [
            "## Module 1.1: What is AI Engineering?",
            "AI Engineering combines software engineering practices with machine learning to build production-ready AI systems. Unlike research ML, AI Engineering focuses on scalability and reliability, integration with existing systems, monitoring and maintenance, and cost optimization.",
            
            "## Module 1.2: The RAG Architecture",
            "Retrieval-Augmented Generation (RAG) is a technique that enhances LLM responses by retrieving relevant context from a knowledge base.",
            
            "The RAG pipeline consists of:",
            "- Document Ingestion: PDFs are parsed and split into chunks",
            "- Embedding Generation: Each chunk is converted to a vector",
            "- Vector Storage: Embeddings stored in a vector database",
            "- Query Processing: User questions are embedded and matched",
            "- Response Generation: Retrieved context passed to an LLM",
            
            "## Module 1.3: Key Components",
            "- Embedding Model: text-embedding-3-small (1536 dimensions)",
            "- LLM: DeepSeek R1 via Azure AI Foundry",
            "- Vector DB: MongoDB Atlas with $vectorSearch",
            "- Interface: Discord Bot using discord.py",
            
            "## Module 1.4: Best Practices",
            "- Chunk size: 500-1000 tokens with overlap",
            "- Similarity threshold: 0.5-0.7 (configurable)",
            "- Context limit: 3-6 most relevant chunks",
            "- Always cite sources in responses",
        ]
    )
    
    # 3. Training Notes Week 2
    create_pdf(
        "training_week2_embeddings.pdf",
        "Week 2: Understanding Embeddings",
        [
            "## Module 2.1: What are Embeddings?",
            "Embeddings are dense vector representations of text that capture semantic meaning. Similar texts have similar embeddings, enabling semantic search.",
            
            "## Module 2.2: Embedding Models",
            "OpenAI text-embedding-3-small: 1536 dimensions, good balance of quality and cost. OpenAI text-embedding-3-large: 3072 dimensions, higher quality but more expensive.",
            
            "## Module 2.3: Cosine Similarity",
            "Cosine similarity measures the angle between two vectors. A score of 1.0 means identical direction, 0.0 means orthogonal, and -1.0 means opposite. For text embeddings, we typically use thresholds between 0.5 and 0.8.",
            
            "## Module 2.4: Chunking Strategies",
            "Fixed-size chunking: Split text into N-token chunks. Paragraph-based: Split on natural paragraph boundaries. Semantic chunking: Use embeddings to find natural break points.",
            
            "## Module 2.5: Hands-on Lab",
            "In this lab, you will generate embeddings for sample documents, compute similarity scores between queries and documents, and implement a basic semantic search function.",
        ]
    )
    
    # 4. Training Notes Week 3
    create_pdf(
        "training_week3_vector_databases.pdf",
        "Week 3: Vector Databases",
        [
            "## Module 3.1: Why Vector Databases?",
            "Traditional databases use exact matching. Vector databases use approximate nearest neighbor (ANN) search to find similar vectors efficiently.",
            
            "## Module 3.2: MongoDB Atlas Vector Search",
            "MongoDB Atlas provides $vectorSearch aggregation pipeline stage. It supports cosine, euclidean, and dot product similarity. Create a search index on your embedding field.",
            
            "## Module 3.3: Index Configuration",
            "Example vector index definition:",
            "- numDimensions: 1536 (match your embedding model)",
            "- similarity: cosine (most common for text)",
            "- path: embedding (field containing vectors)",
            
            "## Module 3.4: Query Example",
            "Use $vectorSearch to find the top K most similar documents. Filter results by metadata (e.g., source document). Return similarity scores for ranking.",
            
            "## Module 3.5: Performance Tips",
            "- Index only the fields you need",
            "- Use filters to reduce search space",
            "- Limit results to top 5-10 matches",
            "- Monitor query latency in production",
        ]
    )
    
    # 5. Project Guidelines
    create_pdf(
        "project_guidelines.pdf",
        "Final Project Guidelines",
        [
            "## Project Overview",
            "Build a production-ready RAG chatbot that answers questions about a domain of your choice. The project should demonstrate understanding of the full RAG pipeline.",
            
            "## Requirements",
            "- Ingest at least 10 PDF documents",
            "- Implement semantic search with configurable threshold",
            "- Include conversation memory for multi-turn dialogue",
            "- Add authentication for admin features",
            "- Write unit tests with at least 80% coverage",
            "- Deploy to a cloud platform (Azure, AWS, or GCP)",
            
            "## Grading Criteria",
            "- Code Quality: 25%",
            "- Functionality: 30%",
            "- Documentation: 20%",
            "- Testing: 15%",
            "- Presentation: 10%",
            
            "## Submission",
            "Submit your GitHub repository link and a 5-minute demo video. Due date: End of Week 12.",
            
            "## Office Hours",
            "Wednesdays 2-4 PM EST. Contact: bootcamp-support@example.com",
        ]
    )
    
    print(f"\nDone! Generated 5 test PDFs in {DATA_DIR}")
    print("Run 'python ingest.py' to load them into the knowledge base.")


if __name__ == "__main__":
    main()
