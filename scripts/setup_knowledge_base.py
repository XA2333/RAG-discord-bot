"""
Knowledge Base Setup Script

This script helps users set up their knowledge base by:
1. Creating the data/ directory if it doesn't exist
2. Optionally downloading sample AI Bootcamp materials
3. Providing instructions for adding custom PDFs

Usage:
    python scripts/setup_knowledge_base.py [--download-samples]
"""

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Sample content for demonstration (creates small PDFs with FAQ content)
SAMPLE_FAQ_CONTENT = """
AI Bootcamp Frequently Asked Questions

Q: What is the AI Bootcamp?
A: The AI Bootcamp is a comprehensive training program designed to teach participants 
   the fundamentals of artificial intelligence, machine learning, and practical 
   applications using modern tools and frameworks.

Q: What are the prerequisites?
A: Basic programming knowledge (preferably Python), understanding of mathematics 
   (linear algebra, statistics), and familiarity with command line tools.

Q: How long is the program?
A: The standard bootcamp runs for 12 weeks, with approximately 10-15 hours of 
   commitment per week including lectures, labs, and projects.

Q: What topics are covered?
A: Week 1-3: Python fundamentals and data manipulation
   Week 4-6: Machine learning basics with scikit-learn
   Week 7-9: Deep learning with PyTorch/TensorFlow
   Week 10-12: NLP, RAG systems, and deployment

Q: What tools will we use?
A: Python 3.10+, Jupyter notebooks, VS Code, Git, Azure AI services, 
   MongoDB Atlas, Discord for collaboration, and GitHub for version control.

Q: How do I get support?
A: Use the Discord bot (!ask command), attend office hours, or post in 
   the discussion forums.
"""

SAMPLE_TRAINING_CONTENT = """
AI Bootcamp Training Notes - Week 1

Module 1: Introduction to AI Engineering

1.1 What is AI Engineering?
AI Engineering combines software engineering practices with machine learning 
to build production-ready AI systems. Unlike research ML, AI Engineering 
focuses on:
- Scalability and reliability
- Integration with existing systems
- Monitoring and maintenance
- Cost optimization

1.2 The RAG Architecture
Retrieval-Augmented Generation (RAG) is a technique that enhances LLM 
responses by retrieving relevant context from a knowledge base:

1. Document Ingestion: PDFs are parsed and split into chunks
2. Embedding Generation: Each chunk is converted to a vector using embedding models
3. Vector Storage: Embeddings are stored in a vector database (MongoDB Atlas)
4. Query Processing: User questions are embedded and matched against stored vectors
5. Response Generation: Retrieved context is passed to an LLM for answer generation

1.3 Key Components
- Embedding Model: text-embedding-3-small (1536 dimensions)
- LLM: DeepSeek R1 via Azure AI Foundry
- Vector DB: MongoDB Atlas with $vectorSearch
- Interface: Discord Bot (discord.py)

1.4 Best Practices
- Chunk size: 500-1000 tokens with overlap
- Similarity threshold: 0.5-0.7 (configurable)
- Context limit: 3-6 most relevant chunks
- Always cite sources in responses
"""


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created data directory: {DATA_DIR}")
    else:
        print(f"✅ Data directory exists: {DATA_DIR}")


def create_sample_txt_files():
    """Create sample text files that can be converted to PDF."""
    samples = {
        "ai_bootcamp_faq.txt": SAMPLE_FAQ_CONTENT,
        "training_notes_week1.txt": SAMPLE_TRAINING_CONTENT,
    }
    
    for filename, content in samples.items():
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"✅ Created: {filename}")
    
    print("\n⚠️  Note: These are .txt files. For PDF ingestion, please:")
    print("    1. Convert these to PDF, OR")
    print("    2. Add your own PDF files to the data/ directory")


def list_current_files():
    """List files currently in the data directory."""
    if not os.path.exists(DATA_DIR):
        print("❌ Data directory does not exist.")
        return
    
    files = os.listdir(DATA_DIR)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    other_files = [f for f in files if not f.lower().endswith('.pdf')]
    
    print(f"\n📂 Files in {DATA_DIR}:")
    print(f"   PDF files: {len(pdf_files)}")
    for f in pdf_files:
        size = os.path.getsize(os.path.join(DATA_DIR, f)) / 1024
        print(f"      - {f} ({size:.1f} KB)")
    
    if other_files:
        print(f"   Other files: {len(other_files)}")
        for f in other_files:
            print(f"      - {f}")


def print_instructions():
    """Print instructions for adding documents."""
    print("\n" + "="*60)
    print("📚 KNOWLEDGE BASE SETUP INSTRUCTIONS")
    print("="*60)
    print("""
To populate your knowledge base with AI Bootcamp materials:

1. OBTAIN YOUR DOCUMENTS
   - Download training PDFs from your course portal
   - Export slides as PDF
   - Save FAQ documents as PDF

2. PLACE FILES IN DATA DIRECTORY
   Copy your PDF files to:
   {data_dir}

3. RUN INGESTION
   After adding PDFs, run the ingestion script:
   
   Windows:  .\\run_ingest.ps1
   Direct:   python ingest.py

4. VERIFY
   Use the Discord bot command: !sources
   This will list all ingested documents.

TIPS:
- Supported format: PDF only
- Maximum file size: 10MB (configurable via MAX_UPLOAD_MB)
- Chunk size is automatic (paragraph-based)
- Re-running ingestion will add new documents
- Use !delete <filename> to remove a document
""".format(data_dir=DATA_DIR))


def main():
    parser = argparse.ArgumentParser(description="Set up Knowledge Base for RAG Bot")
    parser.add_argument('--create-samples', action='store_true', 
                        help='Create sample text files with AI Bootcamp content')
    parser.add_argument('--list', action='store_true',
                        help='List current files in data directory')
    args = parser.parse_args()
    
    print("🚀 RAG Bot Knowledge Base Setup")
    print("-" * 40)
    
    ensure_data_dir()
    
    if args.create_samples:
        create_sample_txt_files()
    
    if args.list or not args.create_samples:
        list_current_files()
    
    print_instructions()


if __name__ == "__main__":
    main()
