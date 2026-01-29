import chromadb
from chromadb.config import Settings
from datetime import datetime
import json

class ConceptMemory:
    def __init__(self, persist_directory="./concept_memory"):
        """Initialize persistent memory for learned concepts"""
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="learned_concepts",
            metadata={"description": "Concepts learned from articles"}
        )
    
    def store_concepts(self, concepts_data, article_url, article_title):
        """
        Store concepts from an article
        
        Args:
            concepts_data: List of dicts with 'name', 'explanation', 'analogy', 'domain'
            article_url: Source URL
            article_title: Article title
        """
        for i, concept in enumerate(concepts_data):
            concept_id = f"{article_url}_{i}_{datetime.now().timestamp()}"
            
            self.collection.add(
                documents=[concept['explanation']],
                metadatas=[{
                    "concept_name": concept['name'],
                    "domain": concept.get('domain', 'General'),  # <-- ADD THIS
                    "analogy": concept.get('analogy', ''),
                    "source_url": article_url,
                    "source_title": article_title,
                    "learned_date": datetime.now().isoformat(),
                }],
                ids=[concept_id]
            )
    
    def check_prior_knowledge(self, concept_name, current_domain=None, threshold=0.7):
        """
        Check if a concept has been learned before
        
        Returns:
            List of related concepts if found, empty list otherwise
        """
        results = self.collection.query(
            query_texts=[concept_name],
            n_results=3
        )
        
        # Filter by similarity threshold (ChromaDB returns distances)
        if results['documents'] and len(results['documents'][0]) > 0:
            related = []
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if 'distances' in results else 0
                
                # Only include if very similar (strict threshold)
                if distance < 0.5:
                    metadata = results['metadatas'][0][i]
                    
                    # Skip if different domain (optional filter)
                    if current_domain:
                        concept_domain = metadata.get('domain', '')
                        if concept_domain and concept_domain != current_domain:
                            continue
                    
                    related.append({
                        'concept': metadata['concept_name'],
                        'explanation': doc,
                        'source': metadata['source_title'],
                        'date': metadata['learned_date']
                    })
            
            return related
        
        return []
    
    def get_all_concepts(self):
        """Get all stored concepts"""
        results = self.collection.get()
        concepts = []
        
        if results['metadatas']:
            for metadata in results['metadatas']:
                concepts.append(metadata['concept_name'])
        
        return concepts
    
    def get_stats(self):
        """Get learning statistics"""
        results = self.collection.get()
        
        if not results['metadatas']:
            return {
                'total_concepts': 0,
                'total_articles': 0,
                'recent_concepts': []
            }
        
        # Count unique articles
        sources = set(m['source_url'] for m in results['metadatas'])
        
        # Get recent concepts (last 5)
        recent = sorted(
            results['metadatas'],
            key=lambda x: x['learned_date'],
            reverse=True
        )[:5]
        
        return {
            'total_concepts': len(results['metadatas']),
            'total_articles': len(sources),
            'recent_concepts': [r['concept_name'] for r in recent]
        }