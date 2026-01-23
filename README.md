# Article Digester

An AI-powered learning tool that transforms dense articles into personalized, digestible content tailored to your learning style and background.

## Problem

Reading technical articles and research papers is challenging when:

- Dense text is hard to absorb and requires multiple re-reads
- Generic explanations don't connect to your existing knowledge
- You need concrete analogies that match your learning style
- Complex concepts lack intuitive explanations

## Solution

Article Digester uses a multi-agent AI system to process articles and generate:

- **Structured breakdowns** - Articles split into clear, logical sections
- **Personalized analogies** - Complex concepts explained using your interests and background
- **Active recall questions** - Test comprehension and reinforce learning
- **Saved outputs** - Build a library of processed articles for future reference

## Features

- **URL Processing** - Extract and process articles from any web URL
- **Personalized Learning** - Adapts explanations based on your background, interests, and learning style
- **Multi-Agent Pipeline** - Separate AI agents for section breakdown, concept simplification, and question generation
- **Persistent Storage** - Saves processed articles as markdown files for future reference
- **Interactive Setup** - One-time configuration that remembers your preferences

## Tech Stack

- **Python 3.10+**
- **LangChain** - Agent orchestration and LLM integration
- **OpenAI GPT-3.5** - Language model for content generation
- **newspaper3k** - Article extraction from URLs

## Why I Built This

As a CS and Cognitive Sciences student, I love learning but struggle with traditional article formats. I often spend time re-reading the same content without absorbing it. This tool was built to transform how I consume technical content by:

- Adapting to my learning style (concrete examples and analogies)
- Connecting new concepts to my existing knowledge
- Making dense material more approachable and memorable
