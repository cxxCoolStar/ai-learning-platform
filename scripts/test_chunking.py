import asyncio
import sys
import os
import logging
import uuid
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import html2text

# Add project root to path
sys.path.append(os.getcwd())

from app.services.crawler import CrawlerFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chunking_strategy():
    url = "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents"
    print(f"--- Testing Chunking for: {url} ---")
    
    # 1. Crawl
    print("\n1. Crawling URL...")
    crawler = CrawlerFactory.get_crawler(url)
    try:
        raw_data = await crawler.crawl(url)
        print(f"Crawl successful. Content length: {len(raw_data.get('content', ''))} chars")
    except Exception as e:
        print(f"Crawl failed: {e}")
        return

    # 2. Convert to Markdown (Simulating Ingestion Logic)
    print("\n2. Converting to Markdown...")
    raw_content = raw_data.get("content", "")
    html_source = raw_data.get("html", "")
    
    content_to_split = raw_content
    is_markdown = False
    
    if html_source and len(html_source) > 100:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0 # Don't wrap lines
        try:
            content_to_split = h.handle(html_source)
            is_markdown = True
            print("Successfully converted HTML to Markdown.")
            # Print preview of Markdown
            print(f"\nMarkdown Preview (First 500 chars):\n{'-'*30}\n{content_to_split[:500]}\n{'-'*30}")
        except Exception as e:
            print(f"HTML to Markdown conversion failed: {e}")

    # 3. Apply Chunking Strategy
    print("\n3. Applying Chunking Strategy...")
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    
    final_chunks = []
    
    if is_markdown:
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_docs = markdown_splitter.split_text(content_to_split)
        
        print(f"Markdown Splitter produced {len(md_docs)} initial chunks based on headers.")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        for doc in md_docs:
            if len(doc.page_content) > 1000:
                sub_chunks = text_splitter.split_documents([doc])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(doc)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        final_chunks = text_splitter.create_documents([content_to_split])

    # 4. Print Results
    print(f"\n--- Final Result: {len(final_chunks)} Chunks Generated ---")
    for i, chunk in enumerate(final_chunks):
        print(f"\n[Chunk {i+1}] Length: {len(chunk.page_content)}")
        print(f"Metadata: {chunk.metadata}")
        print(f"Content Preview: {chunk.page_content[:150]}...")
        if i >= 4: # Only print first 5 to avoid flooding terminal
            print("\n... (Remaining chunks omitted) ...")
            break

if __name__ == "__main__":
    asyncio.run(test_chunking_strategy())
