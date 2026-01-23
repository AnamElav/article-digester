import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from newspaper import Article
from datetime import datetime

def get_user_context():
    """Get or load user context for personalized explanations"""
    context_file = "user_context.json"
    
    # Check if context already exists
    if os.path.exists(context_file):
        with open(context_file, 'r') as f:
            context = json.load(f)
            print("✓ Loaded your existing profile\n")
            return context
    
    # If not, ask user for context
    print("=== FIRST TIME SETUP ===")
    print("To give you better explanations, I need to know a bit about you.\n")
    
    context = {}
    
    context['background'] = input("What's your educational/professional background? (e.g., 'CS student', 'biology researcher', 'high school student')\n> ")
    
    context['interests'] = input("\nWhat are some of your interests or hobbies? (e.g., 'sports, anime, cooking')\n> ")
    
    context['learning_style'] = input("\nHow do you learn best? (e.g., 'concrete examples', 'visual diagrams', 'step-by-step')\n> ")
    
    context['technical_level'] = input("\nHow would you rate your technical/analytical skills? (beginner/intermediate/advanced)\n> ")
    
    # Save for next time
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    print("\n✓ Profile saved! You can edit user_context.json anytime to update.\n")
    return context

def format_user_context(context):
    """Convert context dict into a readable string for the prompt"""
    return f"""
Background: {context.get('background', 'Not specified')}
Interests: {context.get('interests', 'Not specified')}
Learning style: {context.get('learning_style', 'Not specified')}
Technical level: {context.get('technical_level', 'Not specified')}
"""

load_dotenv()
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

def extract_article_from_url(url):
    """Extract article text from URL with error handling"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        if not article.text or len(article.text) < 100:
            raise Exception("Article text is too short or empty")
            
        return article.text, article.title or "Untitled"
    
    except Exception as e:
        print(f"Error extracting article: {str(e)}")
        print("Please check the URL and try again.")
        return None, None

def break_into_sections(article_text):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that breaks down complex articles into digestible sections."),
        ("user", """Break this article into 3-5 main sections. 
        For each section:
        - Give it a clear, descriptive header
        - Write a 1-2 sentence summary of what it covers
        
        Format your response like this:
        
        ## Section 1: [Header]
        [Summary]
        
        ## Section 2: [Header]
        [Summary]
        
        Article:
        {article}""")
    ])

    chain = prompt | llm
    response = chain.invoke({"article": article_text})
    return response.content

def simplify_concepts(text, user_context):
    context_str = format_user_context(user_context)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful assistant that explains complex concepts using concrete, specific analogies tailored to the reader.

Reader profile:
{context_str}

Your job is to make concepts click for THIS specific person. Use their interests and background to create analogies that resonate with them personally."""),
        ("user", """Read this text and identify 2-3 complex, abstract, or unfamiliar concepts that would benefit from explanation.

For each concept:
1. Quote the specific term or idea
2. Explain it in plain language first
3. Create an analogy that:
   - Connects to the reader's interests or background when relevant
   - Uses concrete, familiar examples from everyday life
   - Actually illuminates HOW the concept works, not just what it's similar to
   - Avoids generic/cliché comparisons

IMPORTANT: A good analogy should make someone think "oh, NOW I get it" - not just "that's an interesting comparison."

Format:

**Concept: [exact term from text]**
Explanation: [clear definition in plain language]
Analogy: [specific, personalized comparison that actually helps understanding]

Text:
{text}""")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"text": text})
    return response.content

def generate_questions(article_text):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that creates active recall questions."),
        ("user", """Based on this article, generate 3-5 questions that test comprehension of the key ideas.
        Make them specific, not generic.
        
        Article:
        {article}""")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"article": article_text})
    return response.content

def process_article(article_text, article_title, user_context):
    """Process article with error handling"""
    try:
        print("=== BREAKING INTO SECTIONS ===\n")
        sections = break_into_sections(article_text)
        print(sections)
        
        print("\n=== SIMPLIFYING CONCEPTS ===\n")
        simplified = simplify_concepts(article_text, user_context)
        print(simplified)
        
        print("\n=== RECALL QUESTIONS ===\n")
        questions = generate_questions(article_text)
        print(questions)
        
        return sections, simplified, questions
        
    except Exception as e:
        print(f"\nError processing article: {str(e)}")
        print("This might be due to API issues or article complexity.")
        return None, None, None

def save_to_markdown(url, title, sections, concepts, questions):
    """Save processed article to markdown file"""
    # Create output directory if it doesn't exist
    os.makedirs("processed_articles", exist_ok=True)
    
    # Generate filename from date and title
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '-')[:50]  # Limit length
    filename = f"processed_articles/{date_str}_{safe_title}.md"
    
    # Create markdown content
    content = f"""# {title}

**Source:** {url}  
**Processed:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## Article Breakdown

{sections}

---

## Concept Explanations

{concepts}

---

## Review Questions

{questions}
"""
    
    # Save file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename

if __name__ == "__main__":
    try:
        # Get user context (first time or load existing)
        user_context = get_user_context()
        
        # Get article URL
        url = input("\nPaste article URL: ").strip()
        
        if not url:
            print("No URL provided")
            exit(1)
        
        print(f"\n📥 Extracting article from: {url}\n")
        article_text, article_title = extract_article_from_url(url)
        
        if not article_text:
            exit(1)
        
        print(f"✓ Extracted: {article_title}\n")
        print(f"Article length: {len(article_text)} characters\n")
        
        # Process the article
        sections, concepts, questions = process_article(article_text, article_title, user_context)
        
        if sections and concepts and questions:
            # Save to markdown
            filename = save_to_markdown(url, article_title, sections, concepts, questions)
            print(f"\nSaved to: {filename}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Please check your setup and try again.")




