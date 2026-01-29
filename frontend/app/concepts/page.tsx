"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Concept {
  id: string;
  name: string;
  domain: string;
  source: string;
  source_url: string;
  learned_date: string;
  explanation: string;
  analogy: string;
}

interface Stats {
  total_concepts: number;
  total_articles: number;
  concepts_by_domain: Record<string, number>;
  recent_concepts: string[];
}

export default function ConceptsPage() {
  const router = useRouter();
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedConcepts, setExpandedConcepts] = useState<Set<string>>(
    new Set(),
  );

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("token");

    if (!token) {
      router.push("/login");
      return;
    }

    fetchData();
  }, [router]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");

      const [conceptsRes, statsRes] = await Promise.all([
        fetch("http://localhost:8000/api/concepts", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://localhost:8000/api/stats", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      const conceptsData = await conceptsRes.json();
      const statsData = await statsRes.json();

      setConcepts(conceptsData.concepts);
      setStats(statsData);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (conceptId: string) => {
    setExpandedConcepts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(conceptId)) {
        newSet.delete(conceptId);
      } else {
        newSet.add(conceptId);
      }
      return newSet;
    });
  };

  // Filter concepts
  const filteredConcepts = concepts.filter((concept) => {
    const matchesDomain =
      selectedDomain === "all" || concept.domain === selectedDomain;
    const matchesSearch =
      concept.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      concept.explanation.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  const domains = stats ? Object.keys(stats.concepts_by_domain) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your concepts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-blue-600 hover:text-blue-700 mb-4 inline-block"
          >
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-semibold text-gray-800 mb-2">
            Your Knowledge Library
          </h1>
          <p className="text-gray-600">
            Concepts you've learned from articles and PDFs
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {stats.total_concepts}
              </div>
              <div className="text-gray-600">Concepts Learned</div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {stats.total_articles}
              </div>
              <div className="text-gray-600">Articles Processed</div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {domains.length}
              </div>
              <div className="text-gray-600">Knowledge Domains</div>
            </div>
          </div>
        )}

        {/* Domain Distribution */}
        {stats && stats.concepts_by_domain && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Concepts by Domain
            </h2>
            <div className="space-y-3">
              {Object.entries(stats.concepts_by_domain)
                .sort(([, a], [, b]) => b - a)
                .map(([domain, count]) => (
                  <div key={domain}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700 font-medium">
                        {domain}
                      </span>
                      <span className="text-gray-600">{count} concepts</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(count / stats.total_concepts) * 100}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Concepts
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or description..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Domain
              </label>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Domains</option>
                {domains.map((domain) => (
                  <option key={domain} value={domain}>
                    {domain}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Concepts List */}
        <div className="space-y-4">
          {filteredConcepts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-600">
                {searchQuery || selectedDomain !== "all"
                  ? "No concepts match your filters"
                  : "No concepts learned yet. Process your first article!"}
              </p>
            </div>
          ) : (
            filteredConcepts.map((concept) => {
              const isExpanded = expandedConcepts.has(concept.id);

              return (
                <div
                  key={concept.id}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => toggleExpanded(concept.id)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-1">
                        {concept.name}
                      </h3>
                      <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        {concept.domain}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-500">
                        {new Date(concept.learned_date).toLocaleDateString()}
                      </span>
                      <button className="text-gray-400 hover:text-gray-600">
                        {isExpanded ? (
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 15l7-7 7 7"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 9l-7 7-7-7"
                            />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>

                  <p className="text-gray-700 mb-3">
                    {isExpanded
                      ? concept.explanation
                      : concept.explanation.length > 200
                        ? concept.explanation.substring(0, 200) + "..."
                        : concept.explanation}
                  </p>

                  {/* Show analogy if it exists and concept is expanded */}
                  {concept.analogy && isExpanded && (
                    <div className="bg-blue-50 p-4 rounded-lg mb-3">
                      <div className="text-sm font-semibold text-blue-800 mb-2">
                        💡 Your Personalized Analogy:
                      </div>
                      <p className="text-gray-700 italic">{concept.analogy}</p>
                    </div>
                  )}

                  <div className="text-sm text-gray-600">
                    <span className="font-medium">From:</span>{" "}
                    <span className="italic">{concept.source}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
