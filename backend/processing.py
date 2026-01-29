import json
import os
import re
import requests
import sys
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from newspaper import Article
from datetime import datetime
from memory import ConceptMemory
from pypdf import PdfReader
from io import BytesIO

# Add parent directory to path so we can import memory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

memory = ConceptMemory()

def parse_concepts(concepts_text):
    """
    Parse the LLM's concept output into structured data
    
    Returns list of dicts: [{'name': '...', 'explanation': '...', 'analogy': '...'}]
    """
    concepts = []
    
    # Split by **Concept: pattern
    sections = re.split(r'\*\*Concept:\s*', concepts_text)
    
    for section in sections[1:]:  # Skip first empty split
        try:
            # Extract concept name (up to **)
            name_match = re.search(r'^(.+?)\*\*', section)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # Extract explanation
            exp_match = re.search(r'Explanation:\s*(.+?)(?=Analogy:|$)', section, re.DOTALL)
            explanation = exp_match.group(1).strip() if exp_match else ""
            
            # Extract analogy
            anal_match = re.search(r'Analogy:\s*(.+?)(?=$)', section, re.DOTALL)
            analogy = anal_match.group(1).strip() if anal_match else ""
            
            concepts.append({
                'name': name,
                'explanation': explanation,
                'analogy': analogy
            })
        except Exception as e:
            print(f"Warning: Could not parse concept section: {str(e)}")
            continue
    
    return concepts

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

def extract_from_pdf(pdf_source):
    """
    Extract text from PDF file or URL
    
    Args:
        pdf_source: Either a file path or URL to PDF
    
    Returns:
        (text, title) tuple
    """
    try:
        # Check if it's a URL or file path
        if pdf_source.startswith('http://') or pdf_source.startswith('https://'):
            # Download PDF from URL
            response = requests.get(pdf_source)
            pdf_file = BytesIO(response.content)
            reader = PdfReader(pdf_file)
            title = pdf_source.split('/')[-1].replace('.pdf', '')
        else:
            # Local file path
            reader = PdfReader(pdf_source)
            title = pdf_source.split('/')[-1].replace('.pdf', '')
        
        # Extract text from all pages
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        
        if not text or len(text) < 100:
            raise Exception("PDF text is too short or empty")
        
        # Try to get title from PDF metadata
        if reader.metadata and reader.metadata.get('/Title'):
            title = reader.metadata.get('/Title')
        
        return text, title
        
    except Exception as e:
        print(f"❌ Error extracting PDF: {str(e)}")
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
    """Generate concept explanations, checking memory for prior knowledge"""
    context_str = format_user_context(user_context)
    
    # First, identify concepts with domains
    identify_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that identifies complex concepts."),
        ("user", """Read this text and identify 2-3 complex, abstract, or unfamiliar concepts.
        
        For each concept, provide:
        - Name (2-4 words)
        - Domain/category (e.g., "Databases", "Machine Learning", "Web Development")
        
        Format:
        - Concept Name | Domain
        
        Example:
        - API Gateway | Software Architecture
        - Neural Networks | Machine Learning
        
        Text:
        {text}""")
    ])
    
    chain = identify_prompt | llm
    response = chain.invoke({"text": text})
    
    # Parse response
    concept_entries = []
    for line in response.content.split('\n'):
        if '|' in line:
            parts = line.strip('- ').split('|')
            if len(parts) == 2:
                concept_entries.append({
                    'name': parts[0].strip(),
                    'domain': parts[1].strip()
                })
    
    # Check memory for each concept (with domain filtering)
    prior_knowledge = {}
    for entry in concept_entries:
        related = memory.check_prior_knowledge(
            entry['name'], 
            current_domain=entry['domain']  # <-- PASS DOMAIN
        )
        if related:
            prior_knowledge[entry['name']] = related[0]

    if prior_knowledge:
        relationship_prompt = ChatPromptTemplate.from_messages([
            ("system", "You analyze relationships between concepts."),
            ("user", """Given these previously learned concepts and new concepts, 
            determine which are actually related and how.
            
            Previously learned:
            {prior_concepts}
            
            New concepts from article:
            {new_concepts}
            
            For each new concept, if it's related to a previous concept:
            - State which previous concept it relates to
            - Explain the relationship in one sentence (e.g., "builds on", "contrasts with", "is a specific type of")
            
            If a new concept is unrelated to previous knowledge, say "No prior connection."
            
            Format:
            New Concept | Related To | Relationship
            """)
        ])
        
        prior_concepts_str = "\n".join([
            f"- {info['concept']}: {info['explanation'][:150]}"
            for info in prior_knowledge.values()
        ])
        
        new_concepts_str = "\n".join([f"- {e['name']}" for e in concept_entries])
        
        chain = relationship_prompt | llm
        relationships = chain.invoke({
            "prior_concepts": prior_concepts_str,
            "new_concepts": new_concepts_str
        })
        
        # Parse relationships
        connection_map = parse_relationships(relationships.content)
    else:
        connection_map = {}
    
    # Now generate explanations with specific connections
    explanation_context = ""
    if connection_map:
        explanation_context = "\n\nWhen explaining concepts, use these specific connections:\n"
        for new_concept, (old_concept, relationship) in connection_map.items():
            explanation_context += f"- {new_concept}: {relationship} {old_concept}\n"
    
    # Generate explanations
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You explain concepts using concrete analogies.

Reader profile:
{context_str}
{explanation_context}

For concepts with prior connections, START your explanation by explicitly referencing 
the previous concept. Example: "Remember [old concept]? [New concept] extends that by..."
"""),
        ("user", """Explain these concepts:

{text}

Format:
**Concept: [name]**
Explanation: [if related to prior knowledge, start with "Remember how [prior concept]...?" then explain]
Analogy: [...]
""")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"text": text})
    return response.content, prior_knowledge, concept_entries

def parse_relationships(relationships_text):
    """
    Parse LLM's relationship analysis
    Returns dict: {new_concept: (old_concept, relationship)}
    """
    connection_map = {}
    
    for line in relationships_text.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                new_concept = parts[0]
                related_to = parts[1]
                relationship = parts[2]
                
                if related_to.lower() != "no prior connection":
                    connection_map[new_concept] = (related_to, relationship)
    
    return connection_map

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

def process_article(article_text, article_title, article_url, user_context):
    """Process article with memory integration"""
    try:
        print("=== BREAKING INTO SECTIONS ===\n")
        sections = break_into_sections(article_text)
        print(sections)
        
        print("\n=== SIMPLIFYING CONCEPTS ===\n")
        simplified, prior_knowledge, concept_entries = simplify_concepts(article_text, user_context)  # <-- ADD concept_entries
        print(simplified)
        
        # Show what was remembered
        if prior_knowledge:
            print("\n💡 Building on concepts you already know:")
            for concept, info in prior_knowledge.items():
                print(f"  - {info['concept']} (from {info['source']})")
        
        print("\n=== RECALL QUESTIONS ===\n")
        questions = generate_questions(article_text)
        print(questions)
        
        # Parse and store new concepts
        parsed_concepts = parse_concepts(simplified)
        
        # Add domain info from identification phase
        for i, concept in enumerate(parsed_concepts):
            if i < len(concept_entries):
                concept['domain'] = concept_entries[i]['domain']  # <-- ADD THIS
        
        if parsed_concepts:
            memory.store_concepts(parsed_concepts, article_url, article_title)
            print(f"\n✅ Stored {len(parsed_concepts)} new concepts to memory")
        
        return sections, simplified, questions
        
    except Exception as e:
        print(f"\n❌ Error processing article: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

def save_to_markdown(url, title, sections, concepts, questions):
    """Save processed article to markdown file"""
    # Save to parent directory's processed_articles
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "processed_articles")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename from date and title
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '-')[:50]  # Limit length
    filename = os.path.join(output_dir, f"{date_str}_{safe_title}.md")
    
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

# Add this new function that accepts user_id
def process_article_with_user(article_text, article_title, article_url, user_context, user_id):
    """Process article with user-specific memory"""
    from memory import ConceptMemory
    
    # Use user-specific memory
    user_memory = ConceptMemory(user_id=user_id)
    
    # Temporarily replace global memory with user memory
    global memory
    old_memory = memory
    memory = user_memory
    
    try:
        result = process_article(article_text, article_title, article_url, user_context)
        return result
    finally:
        memory = old_memory

