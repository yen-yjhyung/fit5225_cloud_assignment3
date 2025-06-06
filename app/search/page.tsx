'use client';

import { useRouter } from 'next/navigation';
import { FiLogOut, FiSearch, FiUser, FiX } from 'react-icons/fi';
import { signOut } from '@/lib/auth';
import { useState, FormEvent } from 'react';
import { useAuthTokens, Tokens } from '@/hooks/useAuthTokens';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import Navbar from '@/components/Navbar';

type ApiItem = {
    id: string;
    mediaType: 'image' | 'video' | 'audio';
    thumbnailLink?: string;
    s3Link: string;
    userId: string;
    uploadedAt: string;
    tags: { name: string; count: string }[];
};

type SearchResult = {
    images: ApiItem[];
    videos: ApiItem[];
    audio: ApiItem[];
};

type SpeciesFilter = {
    name: string;
    count: number;
};

export default function SearchPage() {

    const router = useRouter();

    // Input fields for adding species filters
    const [inputSpeciesName, setInputSpeciesName] = useState('');
    const [inputSpeciesCount, setInputSpeciesCount] = useState<number>(1);

    // Array of species filters
    const [speciesFilters, setSpeciesFilters] = useState<SpeciesFilter[]>([]);

    // State for search results, loading indicator, and error message
    const [results, setResults] = useState<SearchResult>({
        images: [],
        videos: [],
        audio: [],
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Active tab: 'images' | 'videos' | 'audio'
    const [activeTab, setActiveTab] = useState<'images' | 'videos' | 'audio'>(
        'images'
    );

    // Retrieve tokens from Cognito via custom hook
    const tokens: Tokens = useAuthTokens();

    // Check if user session is valid
    const { checking } = useCurrentUser();
          
    if (checking)
    return (
        <div>
        <h1 className="text-center text-2xl font-bold mt-20">
            Checking Session...
        </h1>
        </div>
    );

    // Base URL of your API Gateway (no trailing slash)
    const API_BASE = process.env.NEXT_PUBLIC_API_URL;

    const handleNavigation = (path: string) => {
        router.push(path);
    };

    const handleLogout = () => {
        signOut();
        router.push('/auth/login');
    };

    // Add a new species filter, preventing duplicates
    const addSpeciesFilter = () => {
        const name = inputSpeciesName.trim().toLowerCase();
        if (!name || inputSpeciesCount < 1) return;
        if (speciesFilters.some((f) => f.name === name)) {
            setInputSpeciesName('');
            return;
        }
        setSpeciesFilters([
            ...speciesFilters,
            { name, count: inputSpeciesCount },
        ]);
        setInputSpeciesName('');
        setInputSpeciesCount(1);
    };

    // Remove a species filter by name
    const removeSpeciesFilter = (name: string) => {
        setSpeciesFilters(speciesFilters.filter((f) => f.name !== name));
    };

    // Perform search by calling protected API Gateway endpoint
    const handleSearch = async (e: FormEvent) => {
        e.preventDefault();
        if (!API_BASE) {
            setError('API URL is not configured.');
            return;
        }
        if (speciesFilters.length === 0) {
            setError('Please add at least one bird filter.');
            return;
        }
        setError(null);
        setLoading(true);

        try {
            const idToken = tokens.idToken;
            if (!idToken) {
                throw new Error('No ID token available. Please log in again.');
            }

            const resp = await fetch(`${API_BASE}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${idToken}`,
                },
                body: JSON.stringify({ species: speciesFilters }),
            });

            if (!resp.ok) {
                throw new Error(`Server responded with HTTP ${resp.status}`);
            }

            // Expect payload: { results: ApiItem[] }
            const payload: { results: ApiItem[] } = await resp.json();
            const items = payload.results || [];

            // Split items into images, videos, and audio arrays
            const images: ApiItem[] = [];
            const videos: ApiItem[] = [];
            const audio: ApiItem[] = [];
            items.forEach((it) => {
                if (it.mediaType === 'image') {
                    images.push(it);
                } else if (it.mediaType === 'video') {
                    videos.push(it);
                } else if (it.mediaType === 'audio') {
                    audio.push(it);
                }
            });

            setResults({ images, videos, audio });
            setActiveTab('images');
        } catch (err) {
            console.error(err);
            setError('Search failed. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="flex flex-col min-h-screen bg-cover bg-center bg-no-repeat px-4 py-6 pt-28"
            style={{ backgroundImage: "url('/bird_picture.jpg')" }}
        >
            {/* Top Navigation */}
            <Navbar
                onNavigate={handleNavigation}
                onLogout={handleLogout}
                username={tokens?.name}
            />

            {/* Semi‐transparent Overlay */}
            <div className="absolute inset-0 bg-white/8 z-0" />

            {/* Main Content */}
            <main className="relative z-10 w-full max-w-4xl mx-auto p-10 rounded-xl m-auto bg-white/80 shadow-lg">
                <h2 className="text-2xl font-semibold mb-6">Search Media by Bird Species</h2>

                {/* Filters Form */}
                <form onSubmit={handleSearch} className="space-y-6">
                    <div>
                        <label className="block mb-1 font-medium">
                            Bird Filters (add multiple)
                        </label>
                        <div className="flex items-end space-x-4">
                            {/* Species Name Input */}
                            <div className="flex-1">
                                <label className="block mb-1 text-sm font-medium">
                                    Species Name
                                </label>
                                <input
                                    type="text"
                                    value={inputSpeciesName}
                                    onChange={(e) =>
                                        setInputSpeciesName(e.target.value)
                                    }
                                    placeholder="Enter species name"
                                    className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                                />
                            </div>

                            {/* Count Input */}
                            <div className="w-24">
                                <label className="block mb-1 text-sm font-medium">
                                    Count
                                </label>
                                <input
                                    type="number"
                                    min={1}
                                    value={inputSpeciesCount}
                                    onChange={(e) =>
                                        setInputSpeciesCount(Number(e.target.value))
                                    }
                                    className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                                    placeholder="1"
                                />
                            </div>

                            {/* Add Filter Button */}
                            <button
                                type="button"
                                onClick={addSpeciesFilter}
                                className="bg-red-800 text-white px-4 py-2 rounded hover:bg-red-700 transition"
                            >
                                Add
                            </button>
                        </div>

                        {/* Display Added Filters */}
                        <div className="mt-3 flex flex-wrap gap-2">
                            {speciesFilters.map((f) => (
                                <span
                                    key={f.name}
                                    className="flex items-center bg-red-200 text-red-800 text-sm px-2 py-1 rounded-full"
                                >
                  {f.name}:{f.count}
                                    <FiX
                                        size={14}
                                        className="ml-1 cursor-pointer hover:text-red-600"
                                        onClick={() => removeSpeciesFilter(f.name)}
                                    />
                </span>
                            ))}
                        </div>
                    </div>

                    {/* Display Error if Any */}
                    {error && (
                        <div className="text-red-600 font-medium">{error}</div>
                    )}

                    {/* Search Button */}
                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`flex items-center gap-2 bg-red-800 text-white px-6 py-3 rounded-lg shadow hover:bg-red-700 transition ${
                                loading ? 'opacity-60 cursor-not-allowed' : ''
                            }`}
                        >
                            <FiSearch size={20} />
                            {loading ? 'Searching...' : 'Search'}
                        </button>
                    </div>
                </form>

                {/* Results Section */}
                <div className="mt-10">
                    {/* Tabs */}
                    <div className="flex space-x-4 border-b border-gray-300">
                        <button
                            onClick={() => setActiveTab('images')}
                            className={`pb-2 font-medium ${
                                activeTab === 'images'
                                    ? 'border-b-2 border-red-800 text-red-800'
                                    : 'text-gray-600 hover:text-gray-800'
                            }`}
                        >
                            Images
                        </button>
                        <button
                            onClick={() => setActiveTab('videos')}
                            className={`pb-2 font-medium ${
                                activeTab === 'videos'
                                    ? 'border-b-2 border-red-800 text-red-800'
                                    : 'text-gray-600 hover:text-gray-800'
                            }`}
                        >
                            Videos
                        </button>
                        <button
                            onClick={() => setActiveTab('audio')}
                            className={`pb-2 font-medium ${
                                activeTab === 'audio'
                                    ? 'border-b-2 border-red-800 text-red-800'
                                    : 'text-gray-600 hover:text-gray-800'
                            }`}
                        >
                            Audio
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="mt-6">
                        {activeTab === 'images' && (
                            <div className="grid grid-cols-3 gap-4">
                                {results.images.length === 0 ? (
                                    <p className="col-span-3 text-center text-gray-500">
                                        No image results
                                    </p>
                                ) : (
                                    results.images.map((item) => (
                                        <div
                                            key={item.id}
                                            className="rounded overflow-hidden shadow hover:shadow-lg transition cursor-pointer"
                                        >
                                            {/* Thumbnail: click opens full image in new tab */}
                                            <img
                                                src={item.thumbnailLink}
                                                alt={`Thumbnail of ${item.id}`}
                                                className="w-full h-40 object-cover"
                                                onClick={() =>
                                                    window.open(item.s3Link, '_blank')
                                                }
                                            />
                                            <p className="p-2 text-sm font-medium text-gray-800">
                                                {`Resource ID: ${item.id}`}
                                            </p>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {activeTab === 'videos' && (
                            <div className="space-y-4">
                                {results.videos.length === 0 ? (
                                    <p className="text-center text-gray-500">
                                        No video results
                                    </p>
                                ) : (
                                    results.videos.map((item) => (
                                        <div
                                            key={item.id}
                                            className="flex items-center justify-between bg-gray-50 rounded px-4 py-3 shadow hover:bg-gray-100 transition"
                                        >
                                            <div>
                                                <p className="text-gray-800 font-medium">{`Resource ID: ${item.id}`}</p>
                                                <p className="text-sm text-gray-600">{`Tags: ${item.tags
                                                    .map((t) => `${t.name}(${t.count})`)
                                                    .join(', ')}`}</p>
                                            </div>
                                            {/* Simple link to open video in new tab */}
                                            <a
                                                href={item.s3Link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-red-800 hover:underline"
                                            >
                                                View Video
                                            </a>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {activeTab === 'audio' && (
                            <div className="space-y-4">
                                {results.audio.length === 0 ? (
                                    <p className="text-center text-gray-500">
                                        No audio results
                                    </p>
                                ) : (
                                    results.audio.map((item) => (
                                        <div
                                            key={item.id}
                                            className="flex items-center justify-between bg-gray-50 rounded px-4 py-3 shadow hover:bg-gray-100 transition"
                                        >
                                            <div>
                                                <p className="text-gray-800 font-medium">{`Resource ID: ${item.id}`}</p>
                                                <p className="text-sm text-gray-600">{`Tags: ${item.tags
                                                    .map((t) => `${t.name}(${t.count})`)
                                                    .join(', ')}`}</p>
                                            </div>
                                            {/* Simple link to open audio in new tab */}
                                            <a
                                                href={item.s3Link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-red-800 hover:underline"
                                            >
                                                Play Audio
                                            </a>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
