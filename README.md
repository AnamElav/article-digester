# Article Digester

An AI-powered learning tool that transforms dense articles and PDFs into personalized, digestible content tailored to your learning style.

Live Demo: https://article-digester.vercel.app/

## Problem

As a CS and Cognitive Sciences student, I'm always reading papers and technical articles, but I often find myself re-reading the same paragraphs without absorbing them. Generic explanations don't always stick, and I wanted to create something that could adapt to how I actually learn. This tool was built to transform how I consume content by:
- Adapting to my learning style through concrete examples and analogies linked to my interests
- Connecting new concepts to my existing knowledge
- Making dense material more approachable and memorable

## Solution

*Article Digester* is a full-stack web application that processes articles and PDFs using GPT-3.5. It generates structured breakdowns, personalized concept explanations, active recall questions to test comprehension, and a knowledge library that stores learned concepts with domain visualization. 

Key Features:
- Personalized Explanations: Generates analogies based on your specific interests and background
- Semantic Memory System: Uses vector embeddings (ChromaDB) to recognize previously learned concepts, even with different phrasing
- Multi-User Support: Isolated learning data per user with simple token-based authentication
- PDF Processing: Handles both web articles and PDF papers
- Progress Tracking: Visual analytics showing concepts learned by domain, articles processed, and learning velocity

## Tech Stack

Backend:
- FastAPI (Python) - REST API
- LangChain - LLM orchestration
- OpenAI GPT-3.5/4 - Content generation
- ChromaDB - Vector embeddings for semantic search
- Docker - Containerization
Frontend:
- Next.js (TypeScript) - React framework
- Tailwind CSS - Styling
- Vercel - Deployment
  
Infrastructure:
- Google Cloud Run - Serverless container hosting
- Docker - Build and deployment
- Git - Version control
  
## Technical Deep Dive

*Building Effective Memory*

How do you know what concepts a user already understands without storing everything they've ever read? One solution is to use vector embeddings with semantic similarity search.
When a user processes an article, we extract key concepts using LLM and convert these concepts to embeddings (stored in ChromaDB). Then for each new concept, we query existing embeddings and check if the similarity score is above a certain threshold to consider the concept "known". I picked 0.6 for my threshold value because anything lower resulted in false negatives - the system would fail to recognize concepts I'd actually learned before. Higher thresholds (0.7+) were too loose and triggered false positives.
The main challenge was balancing precision and recall. Too strict means you re-learn things you already know. Too loose means the system incorrectly assumes knowledge you don't have. I also needed domain filtering to prevent unrelated concepts from matching - "Structured Logging" shouldn't match with "Columnar Database" just because both involve "structured data."

*Multi-User Support*

This tool was built as a personal tool only meant to be used by myself, friends/family who are interested (5 - 10 users). When multiple users share the same backend, we need a way to easily isolate learning data without getting into the complexity of JWT + passwords. Thus, we let each user get their own ChromaDB collection. For authentication, I used a simple token-based system, in which the token is stored in localStorage and the backend validates the token on each request. 

*Personalization That Actually Works*

Generic analogies don't help anyone learn. When users first use the tool, they are prompted to enter their interests, which are then stored in the backend. This user profile is then injected into the LLM context. Because the analogies map to *existing mental models* rather than introducing new abstractions, the concepts actually stick in my mind. 

## Scaling Considerations

Current Setup (5-10 Users):

Right now, the app runs on GCP Cloud Run with ChromaDB for local storage. Processing costs about $0.10-0.30 per article through OpenAI. For light usage with friends and family, this stays well within Cloud Run's free tier (2M requests/month).

If This Scaled to Hundreds of Users:

- The first bottleneck would be sequential processing, since articles take 30-60 seconds to process, which blocks the user. The solution would be background job queues so users get an instant response and a notification when processing completes.
- The second bottleneck would be cost. At 100 users x 10 articles/month, that's a few hundred dollars a month in OpenAI costs alone. Response caching through Redis could lower this cost by avoiding re-processing the same URLs.
- The third issue is ChromaDB's local file storage doesn't persist across Cloud Run instances. At scale, I'd migrate to a cloud vector database like Postgres with the pgvector extension.
- Finally, without rate limiting, users could spam expensive API calls. Adding per-user quotas (free tier: 10 articles/month, pro tier: unlimited) would prevent abuse.

## What I Learned

- Threshold tuning matters a lot. Semantic similarity doesn't always equal conceptual relationship, and domain filtering is necessary but needs careful design to avoid false negatives.
- There's a huge gap between "works on my laptop" and "works in production." Stateless services are much easier to scale than stateful ones. Cloud Run's auto-scaling handled variable traffic really well without me having to configure anything. Docker is also incredibly easy to use for containerization.
- Every LLM call costs money, so you have to design with that in mind. Although I didn’t build something that I’m seeking to scale, it was good practice to think through what scaling would entail and what challenges I would have to address.
- Working with GCP and Docker for the first time outside an internship gave me hands-on experience with cloud deployment. For my next project, I'm planning to similarly explore AWS in further depth.

## Future Enhancements

- PDF OCR for scanned documents
- Export to Anki/Notion
- Mobile-responsive improvements
- Better error messages

Long-term:
- Progressive knowledge graph showing concept relationships over time
- Spaced repetition scheduling for review questions
- Collaborative learning (share concepts with study groups)
- Analytics dashboard (learning velocity, retention curves)
