EduRAG Pro: Intelligent Educational Platform using RAG
Introduction
EduRAG Pro is a comprehensive educational platform designed for the 8th-grade (Second Intermediate) Mathematics curriculum. I developed this project to address the cumulative nature of mathematics, where mastering fundamental concepts is essential before progressing to advanced topics. The platform utilizes Retrieval-Augmented Generation (RAG) to link raw educational content with the capabilities of Large Language Models, ensuring accurate answers derived exclusively from the official textbook.

Tech Stack
Frontend

Framework: Next.js

Language: TypeScript

Styling: Tailwind CSS

Animation: Framer Motion

Backend

Framework: FastAPI (Python)

Database: SQLite

Vector Search Engine: FAISS (Facebook AI Similarity Search)

AI Architecture
Models and Embeddings

Large Language Model (LLM): Llama 3.3 (70B) via Groq API for high-quality mathematical reasoning.

Embedding Model: paraphrase-multilingual-MiniLM-L12-v2 for accurate processing of Arabic text.

RAG Mechanism

Data Processing: The curriculum is processed using "Semantic Chunking" to maintain the relationship between mathematical laws and their illustrative examples.

Vector Search: User queries are converted into numerical vectors and compared against textbook content stored in FAISS to retrieve the most relevant context.

Response Generation: The LLM is provided only with the retrieved context to ensure accuracy and prevent hallucinations.

Key Features
Teacher Interface

Intelligent Update Report: The system analyzes student performance and links identified learning gaps with specific explanation segments from the textbook to provide precise remedial recommendations.

Quiz Factory: Enables the creation of periodic quizzes based on specific chapters of the curriculum.

Struggling Students Radar: A dashboard highlighting students facing difficulties in specific concepts, with the ability to send targeted Remedial Quizzes.

Student Interface

Contextual Explanations: Students can ask questions and receive direct explanations derived from the curriculum.

Interactive Assessment: Students receive and solve customized quizzes with immediate feedback based on the educational context.

Project Structure
Plaintext
EduRAG_Platform/
├── backend/            # FastAPI engine and RAG logic
│   ├── app/            # Backend source code
│   ├── data/           # Educational content (PDFs)
│   └── rag_data/       # Vector databases (FAISS)
└── frontend/           # Next.js application
    ├── app/            # Pages and routes
    └── components/     # UI components
Installation and Setup
Prerequisites

Python 3.9+

Node.js 18+

Backend Setup

Navigate to the backend directory.

Install dependencies: pip install -r requirements.txt.

Run the server: python main.py.

Frontend Setup

Navigate to the frontend directory.

Install dependencies: npm install.

Run the application: npm run dev.

License
This project is developed for educational and research purposes in the field of AI-driven education.