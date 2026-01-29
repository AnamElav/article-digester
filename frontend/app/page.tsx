"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface ProcessArticleResult {
  article_id: string;
  title: string;
  sections: string;
  concepts: string;
  questions: string;
}

export default function Home() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [source, setSource] = useState("");
  const [sourceType, setSourceType] = useState("url");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProcessArticleResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("token");
    const storedUsername = localStorage.getItem("username");

    if (!token) {
      router.push("/login");
      return;
    }

    setUsername(storedUsername || "");
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    router.push("/login");
  };

  const processArticle = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem("token");

      const response = await fetch(
        "http://localhost:8000/api/process-article",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            source,
            source_type: sourceType,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process article");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Helper function to parse markdown-like formatting
  const formatContent = (text: string) => {
    if (!text) return null;

    // Split by sections (## headers)
    const sections = text.split(/(?=##\s)/);

    return sections.map((section, idx) => {
      // Check if it's a header
      const headerMatch = section.match(/^##\s+(.+?)(\n|$)/);
      if (headerMatch) {
        const title = headerMatch[1];
        const content = section.substring(headerMatch[0].length).trim();

        return (
          <div key={idx} className="mb-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">
              {title}
            </h4>
            <p className="text-gray-700 leading-relaxed">{content}</p>
          </div>
        );
      }

      return (
        <p key={idx} className="text-gray-700 leading-relaxed mb-4">
          {section.trim()}
        </p>
      );
    });
  };

  // Helper to format concepts with bold headers
  const formatConcepts = (text: string) => {
    if (!text) return null;

    // Split by **Concept: pattern
    const concepts = text.split(/(?=\*\*Concept:)/);

    return concepts.map((concept, idx) => {
      if (!concept.trim()) return null;

      // Extract concept name
      const nameMatch = concept.match(/\*\*Concept:\s*(.+?)\*\*/);
      const conceptName = nameMatch ? nameMatch[1] : null;

      // Extract explanation
      const explanationMatch = concept.match(
        /Explanation:\s*(.+?)(?=Analogy:|$)/s,
      );
      const explanation = explanationMatch ? explanationMatch[1].trim() : "";

      // Extract analogy
      const analogyMatch = concept.match(/Analogy:\s*(.+?)(?=$)/s);
      const analogy = analogyMatch ? analogyMatch[1].trim() : "";

      return (
        <div
          key={idx}
          className="mb-6 p-4 bg-white border border-gray-200 rounded-lg"
        >
          {conceptName && (
            <h4 className="text-lg font-bold text-blue-600 mb-3">
              {conceptName}
            </h4>
          )}
          {explanation && (
            <div className="mb-3">
              <span className="text-sm font-semibold text-gray-600">
                Explanation:
              </span>
              <p className="text-gray-700 mt-1 leading-relaxed">
                {explanation}
              </p>
            </div>
          )}
          {analogy && (
            <div className="bg-blue-50 p-3 rounded">
              <span className="text-sm font-semibold text-blue-800">
                Analogy:
              </span>
              <p className="text-gray-700 mt-1 leading-relaxed italic">
                {analogy}
              </p>
            </div>
          )}
        </div>
      );
    });
  };

  // Helper to format questions
  const formatQuestions = (text: string) => {
    if (!text) return null;

    // Split by numbered questions
    const questions = text.split(/\n(?=\d+\.)/);

    return (
      <ol className="space-y-3">
        {questions.map((q, idx) => {
          const cleaned = q.trim().replace(/^\d+\.\s*/, "");
          if (!cleaned) return null;

          return (
            <li key={idx} className="text-gray-700 leading-relaxed pl-2">
              {cleaned}
            </li>
          );
        })}
      </ol>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-semibold text-gray-800 mb-2 tracking-tight">
              Article Digester
            </h1>
            <p className="text-gray-600">Welcome back, {username}!</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-800 text-sm font-medium"
          >
            Logout
          </button>
        </div>

        <div className="flex justify-center mb-6">
          <Link
            href="/concepts"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            View Your Knowledge Library →
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Input Type
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="url">Article URL</option>
              <option value="pdf_url">PDF URL</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              {sourceType === "url" ? "Article URL" : "PDF URL"}
            </label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder={
                sourceType === "url"
                  ? "https://example.com/article"
                  : "https://arxiv.org/pdf/1234.5678.pdf"
              }
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900 placeholder-gray-400"
            />
          </div>

          <button
            onClick={processArticle}
            disabled={loading || !source}
            className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold text-lg transition-colors shadow-md hover:shadow-lg"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing...
              </span>
            ) : (
              "Process Article"
            )}
          </button>
        </div>

        {loading && (
          <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-800 px-6 py-4 rounded-lg mb-6 shadow">
            <div className="flex items-center">
              <svg
                className="animate-spin h-5 w-5 mr-3"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <div>
                <p className="font-semibold">Processing your article...</p>
                <p className="text-sm">This usually takes 30-60 seconds</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-6 py-4 rounded-lg mb-6 shadow">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-8 border-b pb-4">
                {result.title}
              </h2>

              <div className="mb-10">
                <div className="flex items-center mb-4">
                  <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold mr-3">
                    1
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">
                    Article Breakdown
                  </h3>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg">
                  {formatContent(result.sections)}
                </div>
              </div>

              <div className="mb-10">
                <div className="flex items-center mb-4">
                  <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold mr-3">
                    2
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">
                    Concept Explanations
                  </h3>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg">
                  {formatConcepts(result.concepts)}
                </div>
              </div>

              <div>
                <div className="flex items-center mb-4">
                  <span className="bg-purple-500 text-white px-3 py-1 rounded-full text-sm font-semibold mr-3">
                    3
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">
                    Review Questions
                  </h3>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg">
                  {formatQuestions(result.questions)}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
