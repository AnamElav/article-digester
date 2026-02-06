from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from users import create_or_get_user, verify_token

load_dotenv()

app = FastAPI(title="Article Digester API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://article-digester.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get current user from token
async def get_current_user(authorization: str = Header(None)):
    """Get user_id from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id

class UserProfile(BaseModel):
    background: str
    interests: str

class UserProfileResponse(BaseModel):
    username: str
    profile: UserProfile | None

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

class LoginRequest(BaseModel):
    username: str

# Auth endpoint
@app.post("/api/login")
async def login(request: LoginRequest):
    """Login or create user (no password needed for trusted users)"""
    user_id, token, is_new = create_or_get_user(request.username)
    
    return {
        "token": token,
        "user_id": user_id,
        "username": request.username,
        "is_new": is_new
    }

# Endpoint to get user profile
@app.get("/api/profile", response_model=UserProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get user profile"""
    from users import load_users
    
    users = load_users()
    user_data = users.get(user_id, {})
    
    profile = user_data.get('profile')
    
    return {
        "username": user_data.get('username', user_id),
        "profile": profile
    }

# Endpoint to save user profile
@app.post("/api/profile")
async def save_profile(
    profile: UserProfile,
    user_id: str = Depends(get_current_user)
):
    """Save user profile"""
    from users import load_users, save_users
    
    users = load_users()
    
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    users[user_id]['profile'] = profile.dict()
    save_users(users)
    
    return {"status": "success", "profile": profile}

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "Article Digester API"}

# Protected: Process article endpoint
@app.post("/api/process-article", response_model=ProcessArticleResponse)
async def process_article_endpoint(
    request: ProcessArticleRequest,
    user_id: str = Depends(get_current_user)
):
    """Process an article or PDF and return structured output"""
    try:
        from processing import (
            extract_article_from_url,
            extract_from_pdf,
            process_article_with_user,
            save_to_markdown
        )
        from users import load_users
        
        # Get user's profile
        users = load_users()
        user_data = users.get(user_id, {})
        user_profile = user_data.get('profile')
        
        # Use user's profile if available, otherwise use defaults
        if user_profile:
            user_context = user_profile
        else:
            # Default context
            user_context = {
                "background": "General",
                "interests": "Technology, learning",
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
        
        # Process article with user-specific memory
        sections, concepts, questions = process_article_with_user(
            article_text,
            article_title,
            request.source,
            user_context,
            user_id,
        )

        # Processing failed (e.g. exception in LLM/memory) — don't return None to Pydantic
        if sections is None or questions is None:
            raise HTTPException(
                status_code=500,
                detail="Article processing failed (sections/questions were None). Check server logs.",
            )

        # Save to markdown
        filename = save_to_markdown(
            request.source, article_title, sections, concepts or "No new concepts", questions
        )

        return ProcessArticleResponse(
            article_id=os.path.basename(filename),
            title=article_title,
            sections=sections,
            concepts=concepts or "No new concepts",
            questions=questions,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Article processing failed: {str(e)}")

# Protected: Get concepts
@app.get("/api/concepts")
async def get_concepts(user_id: str = Depends(get_current_user)):
    """Get all learned concepts for current user"""
    try:
        from memory import ConceptMemory
        memory = ConceptMemory(user_id=user_id)  # User-specific memory
        
        results = memory.collection.get()
        
        if not results['metadatas']:
            return {"concepts": []}
        
        concepts = []
        for i, metadata in enumerate(results['metadatas']):
            concepts.append({
                "id": results['ids'][i],
                "name": metadata.get('concept_name'),
                "domain": metadata.get('domain', 'General'),
                "source": metadata.get('source_title'),
                "source_url": metadata.get('source_url'),
                "learned_date": metadata.get('learned_date'),
                "explanation": results['documents'][i],
                "analogy": metadata.get('analogy', '')
            })
        
        concepts.sort(key=lambda x: x['learned_date'], reverse=True)
        return {"concepts": concepts}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Protected: Get stats
@app.get("/api/stats")
async def get_stats(user_id: str = Depends(get_current_user)):
    """Get learning statistics for current user"""
    try:
        from memory import ConceptMemory
        memory = ConceptMemory(user_id=user_id)  # User-specific memory
        
        results = memory.collection.get()
        
        if not results['metadatas']:
            return {
                "total_concepts": 0,
                "total_articles": 0,
                "concepts_by_domain": {},
                "recent_concepts": []
            }
        
        sources = set(m['source_url'] for m in results['metadatas'])
        
        domain_counts = {}
        for metadata in results['metadatas']:
            domain = metadata.get('domain', 'General')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        recent = sorted(
            results['metadatas'],
            key=lambda x: x.get('learned_date', ''),
            reverse=True
        )[:5]
        
        recent_concepts = [r.get('concept_name') for r in recent]
        
        return {
            "total_concepts": len(results['metadatas']),
            "total_articles": len(sources),
            "concepts_by_domain": domain_counts,
            "recent_concepts": recent_concepts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))