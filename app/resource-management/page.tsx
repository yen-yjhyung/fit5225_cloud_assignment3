'use client';

import { useRouter } from 'next/navigation';
import {
    FiLogOut,
    FiSearch,
    FiUser,
    FiX,
    FiTrash2,
    FiEdit3,
    FiVolume2,
    FiVideo,
} from 'react-icons/fi';
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
    tags: { name: string; count: number }[];
};

type SpeciesFilter = {
    name: string;
    count: number;
};

export default function ResourceManagementPage() {

    // Search filters
    const [inputSpeciesName, setInputSpeciesName] = useState('');
    const [inputSpeciesCount, setInputSpeciesCount] = useState<number>(1);
    const [speciesFilters, setSpeciesFilters] = useState<SpeciesFilter[]>([]);

    // Fetched resources
    const [resources, setResources] = useState<ApiItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Track which item is in "edit tags" mode
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTagName, setEditTagName] = useState('');
    const [editTagCount, setEditTagCount] = useState<number>(1);
    const [editOperation, setEditOperation] = useState<'add' | 'remove'>('add');

    const router = useRouter();

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

    // Base URL of your API Gateway
    const API_BASE = process.env.NEXT_PUBLIC_API_URL;

    const handleNavigation = (path: string) => {
        router.push(path);
    };

    const handleLogout = () => {
        signOut();
        router.push('/auth/login');
    };

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

    const removeSpeciesFilter = (name: string) => {
        setSpeciesFilters(speciesFilters.filter((f) => f.name !== name));
    };

    // Fetch resources by species filters
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

            const payload: { results: ApiItem[] } = await resp.json();
            setResources(payload.results || []);
        } catch (err) {
            console.error(err);
            setError('Search failed. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    // Update tags for a specific resource
    const handleUpdateTags = async (item: ApiItem) => {
        if (!API_BASE) return;
        setError(null);

        try {
            const idToken = tokens.idToken;
            if (!idToken) throw new Error('No ID token. Please log in again.');

            // Build update payload: url array contains the thumbnailLink
            const payload = {
                url: [item.thumbnailLink!],
                operation: editOperation,
                tags: [{ name: editTagName.trim().toLowerCase(), count: editTagCount }],
            };

            const resp = await fetch(`${API_BASE}/update-tags`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${idToken}`,
                },
                body: JSON.stringify(payload),
            });

            if (!resp.ok) {
                throw new Error(`Server responded with HTTP ${resp.status}`);
            }

            // Refresh list
            setEditingId(null);
            await handleSearch(new Event('submit') as any);
        } catch (err) {
            console.error(err);
            setError('Failed to update tags.');
        }
    };

    // Delete a specific resource
    const handleDelete = async (item: ApiItem) => {
        if (!API_BASE) return;
        setError(null);

        const confirm = window.confirm(
            `Are you sure you want to delete resource ${item.id}?`
        );
        if (!confirm) return;

        try {
            const idToken = tokens.idToken;
            if (!idToken) throw new Error('No ID token. Please log in again.');

            const payload = { url: item.s3Link };

            const resp = await fetch(`${API_BASE}/delete-resource`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${idToken}`,
                },
                body: JSON.stringify(payload),
            });

            if (!resp.ok) {
                throw new Error(`Server responded with HTTP ${resp.status}`);
            }

            // Remove from local list
            setResources(resources.filter((r) => r.id !== item.id));
        } catch (err) {
            console.error(err);
            setError('Failed to delete resource.');
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
            <main className="relative z-10 w-full max-w-5xl mx-auto p-10 rounded-xl m-auto bg-white/80 shadow-lg">
                <h2 className="text-2xl font-semibold mb-6">Resource Management</h2>

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
                                    onChange={(e) => setInputSpeciesName(e.target.value)}
                                    placeholder="Enter species name"
                                    className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                                />
                            </div>

                            {/* Count Input */}
                            <div className="w-24">
                                <label className="block mb-1 text-sm font-medium">Count</label>
                                <input
                                    type="number"
                                    min={1}
                                    value={inputSpeciesCount}
                                    onChange={(e) => setInputSpeciesCount(Number(e.target.value))}
                                    className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                                    placeholder="1"
                                />
                            </div>

                            {/* Add Filter Button */}
                            <button
                                type="button"
                                onClick={addSpeciesFilter}
                                className="cursor-pointer bg-red-800 text-white px-4 py-2 rounded hover:bg-red-700 transition"
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

                    {/* Error Message */}
                    {error && <div className="text-red-600 font-medium">{error}</div>}

                    {/* Search Button */}
                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`cursor-pointer flex items-center gap-2 bg-red-800 text-white px-6 py-3 rounded-lg shadow hover:bg-red-700 transition ${
                                loading ? 'opacity-60 cursor-not-allowed' : ''
                            }`}
                        >
                            <FiSearch size={20} />
                            {loading ? 'Searching...' : 'Search'}
                        </button>
                    </div>
                </form>

                {/* Results List */}
                <div className="mt-10 space-y-6">
                    {resources.length === 0 ? (
                        <p className="text-center text-gray-500">No resources found.</p>
                    ) : (
                        resources.map((item) => (
                            <div
                                key={item.id}
                                className="bg-white rounded-lg shadow-md p-6 flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0"
                            >
                                {/* Left: Thumbnail or Icon + Info */}
                                <div className="flex items-center space-x-4">
                                    {item.mediaType === 'image' && item.thumbnailLink ? (
                                        <img
                                            src={item.thumbnailLink}
                                            alt={`Thumbnail ${item.id}`}
                                            className="w-24 h-24 object-cover rounded cursor-pointer"
                                            onClick={() => window.open(item.s3Link, '_blank')}
                                        />
                                    ) : item.mediaType === 'video' ? (
                                        <div
                                            className="w-24 h-24 bg-gray-200 flex items-center justify-center rounded cursor-pointer"
                                            onClick={() => window.open(item.s3Link, '_blank')}
                                        >
                                            <FiVideo size={32} className="text-gray-500" />
                                        </div>
                                    ) : (
                                        <div
                                            className="w-24 h-24 bg-gray-200 flex items-center justify-center rounded cursor-pointer"
                                            onClick={() => window.open(item.s3Link, '_blank')}
                                        >
                                            <FiVolume2 size={32} className="text-gray-500" />
                                        </div>
                                    )}
                                    <div>
                                        <p className="font-medium text-gray-800">{`ID: ${item.id}`}</p>
                                        <p className="text-sm text-gray-600">{`Type: ${item.mediaType}`}</p>
                                        <p className="text-sm text-gray-600">{`Tags: ${item.tags
                                            .map((t) => `${t.name}(${t.count})`)
                                            .join(', ')}`}</p>
                                    </div>
                                </div>

                                {/* Right: Actions (Edit tags, Delete resource) */}
                                <div className="flex flex-col space-y-2">
                                    {/* Delete Button with Confirmation */}
                                    <button
                                        onClick={() => handleDelete(item)}
                                        className="flex items-center gap-1 text-red-700 hover:text-red-900"
                                    >
                                        <FiTrash2 size={18} />
                                        Delete
                                    </button>

                                    {/* Edit Tags Toggle */}
                                    <button
                                        onClick={() =>
                                            setEditingId(editingId === item.id ? null : item.id)
                                        }
                                        className="flex items-center gap-1 text-blue-700 hover:text-blue-900"
                                    >
                                        <FiEdit3 size={18} />
                                        {editingId === item.id ? 'Cancel' : 'Edit Tags'}
                                    </button>

                                    {/* Edit Form (shown when editing this item) */}
                                    {editingId === item.id && (
                                        <div className="border border-gray-300 p-3 rounded space-y-2">
                                            <div>
                                                <label className="block mb-1 text-sm font-medium">
                                                    Tag Name
                                                </label>
                                                <input
                                                    type="text"
                                                    value={editTagName}
                                                    onChange={(e) => setEditTagName(e.target.value)}
                                                    placeholder="e.g. crow"
                                                    className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block mb-1 text-sm font-medium">
                                                    Count
                                                </label>
                                                <input
                                                    type="number"
                                                    min={1}
                                                    value={editTagCount}
                                                    onChange={(e) =>
                                                        setEditTagCount(Number(e.target.value))
                                                    }
                                                    className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    placeholder="1"
                                                />
                                            </div>
                                            <div>
                                                <label className="block mb-1 text-sm font-medium">
                                                    Operation
                                                </label>
                                                <select
                                                    value={editOperation}
                                                    onChange={(e) =>
                                                        setEditOperation(e.target.value as 'add' | 'remove')
                                                    }
                                                    className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                >
                                                    <option value="add">Add</option>
                                                    <option value="remove">Remove</option>
                                                </select>
                                            </div>
                                            <button
                                                onClick={() => handleUpdateTags(item)}
                                                className="mt-2 bg-blue-700 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
                                            >
                                                Submit
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </main>
        </div>
    );
}
