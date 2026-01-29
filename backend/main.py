from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Article Digester API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ProcessArticleRequest(BaseModel):
    source: str
    source_type: str
    
class ProcessArticleResponse(BaseModel):
    article_id: str
    title: str
    sections: str
    concepts: str
    questions: str

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "Article Digester API"}

# Process article endpoint
@app.post("/api/process-article", response_model=ProcessArticleResponse)
async def process_article_endpoint(request: ProcessArticleRequest):
    """
    Process an article or PDF and return structured output
    """
    try:
        from processing import (
            extract_article_from_url,
            extract_from_pdf,
            process_article,
            save_to_markdown
        )
        
        # For now, use default user context (auth can be added later)
        user_context = {
            "background": "CS and CogSci senior at Rice",
            "interests": "dance, weightlifting, K-pop, AI/ML",
            "learning_style": "concrete examples, analogies to real systems",
            "technical_level": "advanced"
        }
        
        # Extract content
        if request.source_type == "url":
            article_text, article_title = extract_article_from_url(request.source)
        elif request.source_type == "pdf_url":
            article_text, article_title = extract_from_pdf(request.source)
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
        
        if not article_text:
            raise HTTPException(status_code=400, detail="Could not extract article")
        
        # Process article
        sections, concepts, questions = process_article(
            article_text, 
            article_title, 
            request.source, 
            user_context
        )
        
        # Save to markdown
        filename = save_to_markdown(request.source, article_title, sections, concepts or "No new concepts", questions)
        
        return ProcessArticleResponse(
            article_id=os.path.basename(filename),
            title=article_title,
            sections=sections,
            concepts=concepts or "No new concepts",
            questions=questions
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Get user's processed articles
@app.get("/api/articles")
async def get_articles():
    """
    Get list of all processed articles
    """
    import glob
    
    articles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "processed_articles")
    articles = []
    
    for filepath in glob.glob(f"{articles_dir}/*.md"):
        filename = os.path.basename(filepath)
        articles.append({
            "id": filename,
            "filename": filename
        })
    
    return {"articles": articles}

# Get specific article
@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    """
    Get a specific processed article
    """
    articles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "processed_articles")
    filepath = os.path.join(articles_dir, article_id)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Article not found")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    return {"content": content}