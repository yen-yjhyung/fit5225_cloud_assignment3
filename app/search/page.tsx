'use client';

import {useRouter} from 'next/navigation';
import {FiSearch, FiX, FiUpload, FiFileText, FiVideo, FiVolume2} from 'react-icons/fi';
import {signOut} from '@/lib/auth';
import {useState, FormEvent, ChangeEvent, useRef} from 'react';
import {useAuthTokens, Tokens} from '@/hooks/useAuthTokens';
import {useCurrentUser} from '@/hooks/useCurrentUser';
import Navbar from '@/components/Navbar';

const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB
const SUPPORTED_EXTS: Record<string, string> = {
    '.aac': 'audio/aac',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/x-wav',
    '.bmp': 'image/bmp',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
};

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
    const tokens: Tokens = useAuthTokens();
    const {checking} = useCurrentUser();
    const API_BASE = process.env.NEXT_PUBLIC_API_URL;

    // common state
    const [results, setResults] = useState<SearchResult>({images: [], videos: [], audio: []});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'images' | 'videos' | 'audio'>('images');

    // search mode: 'species', 'file' or 'tag'
    const [mode, setMode] = useState<'species' | 'file' | 'tag'>('tag');

    // species filter state
    const [inputName, setInputName] = useState('');
    const [inputCount, setInputCount] = useState(1);
    const [filters, setFilters] = useState<SpeciesFilter[]>([]);

    // tag-only filter state
    const [tagInput, setTagInput] = useState('');
    const [tagFilters, setTagFilters] = useState<string[]>([]);

    // file upload state
    const [file, setFile] = useState<File | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);

    if (checking) {
        return <div className="text-center text-2xl mt-20 font-bold">Checking session...</div>;
    }

    const handleLogout = () => {
        signOut();
        router.push('/auth/login');
    };
    const handleNav = (path: string) => router.push(path);

    // species handlers
    const addFilter = () => {
        const name = inputName.trim().toLowerCase();
        if (!name || inputCount < 1) return;
        if (filters.find(f => f.name === name)) {
            setInputName('');
            return;
        }
        setFilters([...filters, {name, count: inputCount}]);
        setInputName('');
        setInputCount(1);
    };
    const removeFilter = (name: string) => setFilters(filters.filter(f => f.name !== name));

    // tag-only handlers
    const addTagFilter = () => {
        const name = tagInput.trim().toLowerCase();
        if (!name) return;
        if (tagFilters.includes(name)) {
            setTagInput('');
            return;
        }
        setTagFilters([...tagFilters, name]);
        setTagInput('');
    };
    const removeTagFilter = (name: string) => setTagFilters(tagFilters.filter(t => t !== name));

    // file handlers
    const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        setError(null);
        const f = e.target.files?.[0] || null;
        if (!f) {
            setFile(null);
            return;
        }
        const ext = '.' + f.name.split('.').pop()!.toLowerCase();
        if (!(ext in SUPPORTED_EXTS)) {
            setError(`Supported: ${Object.keys(SUPPORTED_EXTS).join(', ')}`);
            setFile(null);
            return;
        }
        if (f.size > MAX_FILE_SIZE) {
            setError('Max size 2MB');
            setFile(null);
            return;
        }
        setFile(f);
    };
    const triggerSelect = () => fileRef.current?.click();

    // perform species search
    const doSpeciesSearch = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!API_BASE) return setError('API missing');
        if (filters.length === 0) return setError('Add at least one filter');
        setLoading(true);
        setFile(null);
        try {
            const token = tokens.idToken;
            if (!token) throw new Error('Missing token');
            const resp = await fetch(`${API_BASE}/query`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', Authorization: `Bearer ${token}`},
                body: JSON.stringify({species: filters})
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const j: { results: ApiItem[] } = await resp.json();
            splitResults(j.results);
        } catch (err: any) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // perform tag-only search
    const doTagSearch = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!API_BASE) return setError('API missing');
        if (tagFilters.length === 0) return setError('Add at least one tag');
        setLoading(true);
        setFile(null);
        try {
            const token = tokens.idToken;
            if (!token) throw new Error('Missing token');
            const resp = await fetch(`${API_BASE}/find`, {
                method: 'POST', headers: {'Content-Type': 'application/json', Authorization: `Bearer ${token}`},
                body: JSON.stringify({species: tagFilters.map(name => ({name}))})
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const j: { results: ApiItem[] } = await resp.json();
            splitResults(j.results);
        } catch (err: any) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // perform file search
    const doFileSearch = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!API_BASE) return setError('API missing');
        if (!file) return setError('Select a file');
        setLoading(true);
        try {
            const reader = new FileReader();
            reader.onload = async () => {
                const token = tokens.idToken;
                if (!token) throw new Error('Missing token');
                const dataUrl = reader.result as string;
                const base64 = dataUrl.split(',')[1];
                const ext = '.' + file.name.split('.').pop()!.toLowerCase();
                const contentType = SUPPORTED_EXTS[ext];
                const resp = await fetch(`${API_BASE}/query-by-file`, {
                    method: 'POST',
                    headers: { 'Content-Type': contentType, Authorization: `Bearer ${token}` },
                    body: base64
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const j: { results: ApiItem[] } = await resp.json();
                splitResults(j.results);
            };
            reader.readAsDataURL(file);
        } catch (err: any) {
            console.error(err);
            setError(err.message);
        }
        finally {
            setLoading(false);
        }
    };

    // split items into tabs
    const splitResults = (items: ApiItem[]) => {
        const imgs: ApiItem[] = [];
        const vids: ApiItem[] = [];
        const auds: ApiItem[] = [];
        items.forEach(it => {
            if (it.mediaType === 'image') imgs.push(it);
            else if (it.mediaType === 'video') vids.push(it);
            else auds.push(it);
        });
        setResults({images: imgs, videos: vids, audio: auds});
        setActiveTab('images');
    };

    return (
        <div className="flex flex-col min-h-screen bg-cover bg-center px-4 py-6 pt-28"
             style={{backgroundImage: "url('/bird_picture.jpg')"}}>
            <Navbar onNavigate={handleNav} onLogout={handleLogout} username={tokens.name}/>
            <div className="absolute inset-0 bg-white/8"/>
            <main className="relative z-10 w-full max-w-4xl m-auto bg-white/80 p-10 rounded-xl shadow-lg">
                <h2 className="text-2xl font-semibold mb-6">Search Media</h2>
                {/* mode tabs */}
                <div className="flex space-x-4 border-b border-gray-300 mb-6">
                    <button onClick={() => setMode('tag')}
                            className={`pb-2 font-medium ${mode === 'tag' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Search
                        by Tags
                    </button>
                    <button onClick={() => setMode('species')}
                            className={`pb-2 font-medium ${mode === 'species' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Search
                        by Species & Counts
                    </button>
                    <button onClick={() => setMode('file')}
                            className={`pb-2 font-medium ${mode === 'file' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Search
                        by File
                    </button>
                </div>

                {/* search forms */}
                {mode === 'species' && (
                    <form onSubmit={doSpeciesSearch} className="space-y-6">
                        <div>
                            <label className="block mb-1 font-medium">Bird Filters</label>
                            <div className="flex items-end space-x-4">
                                <div className="flex-1">
                                    <label className="block mb-1 text-sm font-medium">Species Name</label>
                                    <input value={inputName} onChange={e => setInputName(e.target.value)}
                                           placeholder="Enter species"
                                           className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"/>
                                </div>
                                <div className="w-24">
                                    <label className="block mb-1 text-sm font-medium">Count</label>
                                    <input type="number" min={1} value={inputCount}
                                           onChange={e => setInputCount(Number(e.target.value))}
                                           className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"/>
                                </div>
                                <button type="button" onClick={addFilter}
                                        className="bg-red-800 text-white px-4 py-2 rounded hover:bg-red-700">Add
                                </button>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                                {filters.map(f => (
                                    <span key={f.name}
                                          className="flex items-center bg-red-200 text-red-800 text-sm px-2 py-1 rounded-full">
                    {f.name}:{f.count}<FiX size={14} className="ml-1 cursor-pointer hover:text-red-600"
                                           onClick={() => removeFilter(f.name)}/>
                  </span>
                                ))}
                            </div>
                        </div>
                        {error && <div className="text-red-600 font-medium">{error}</div>}
                        <button type="submit" disabled={loading}
                                className="flex items-center gap-2 bg-red-800 text-white px-6 py-3 rounded-lg shadow hover:bg-red-700 transition">{loading ? 'Searching...' : <>
                            <FiSearch size={20}/> Search</>}</button>
                    </form>
                )}
                {mode === 'file' && (
                    <form onSubmit={doFileSearch} className="space-y-6">
                        <div>
                            <label className="block mb-1 font-medium">Upload File</label>
                            <input ref={fileRef} type="file" accept={Object.values(SUPPORTED_EXTS).join(',')}
                                   onChange={onFileChange} className="hidden"/>
                            <button type="button" onClick={triggerSelect}
                                    className="flex items-center gap-2 bg-red-800 text-white px-4 py-2 rounded hover:bg-red-700">
                                <FiUpload/> Choose File
                            </button>
                            {file && <div className="flex items-center mt-4"><FiFileText size={20}
                                                                                         className="text-gray-600 mr-2"/><span
                                className="text-gray-800">{file.name}</span></div>}
                            <p className="mt-1 text-sm text-gray-600">Supported: {Object.keys(SUPPORTED_EXTS).join(', ')},
                                max 2MB</p>
                        </div>
                        {error && <div className="text-red-600 font-medium">{error}</div>}
                        <button type="submit" disabled={loading}
                                className="flex items-center gap-2 bg-red-800 text-white px-6 py-3 rounded-lg shadow hover:bg-red-700 transition">{loading ? 'Searching...' : <>
                            <FiSearch size={20}/> Search</>}</button>
                    </form>
                )}
                {mode === 'tag' && (
                    <form onSubmit={doTagSearch} className="space-y-6">
                        <div>
                            <label className="block mb-1 font-medium">Tag Filters</label>
                            <div className="flex items-end space-x-4">
                                <div className="flex-1">
                                    <label className="block mb-1 text-sm font-medium">Tag Name</label>
                                    <input value={tagInput} onChange={e => setTagInput(e.target.value)}
                                           placeholder="Enter tag"
                                           className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"/>
                                </div>
                                <button type="button" onClick={addTagFilter}
                                        className="bg-red-800 text-white px-4 py-2 rounded hover:bg-red-700">Add
                                </button>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                                {tagFilters.map(t => (<span key={t}
                                                            className="flex items-center bg-red-200 text-red-800 text-sm px-2 py-1 rounded-full">{t}<FiX
                                    size={14} className="ml-1 cursor-pointer hover:text-red-600"
                                    onClick={() => removeTagFilter(t)}/></span>))}
                            </div>
                        </div>
                        {error && <div className="text-red-600 font-medium">{error}</div>}
                        <button type="submit" disabled={loading}
                                className="flex items-center gap-2 bg-red-800 text-white px-6 py-3 rounded-lg shadow hover:bg-red-700 transition">{loading ? 'Searching...' : <>
                            <FiSearch size={20}/> Search</>}</button>
                    </form>
                )}

                {/* results tabs and content */}
                <div className="mt-10">
                    <div className="flex space-x-4 border-b border-gray-300">
                        <button onClick={() => setActiveTab('images')}
                                className={`pb-2 font-medium ${activeTab === 'images' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Images
                        </button>
                        <button onClick={() => setActiveTab('videos')}
                                className={`pb-2 font-medium ${activeTab === 'videos' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Videos
                        </button>
                        <button onClick={() => setActiveTab('audio')}
                                className={`pb-2 font-medium ${activeTab === 'audio' ? 'border-b-2 border-red-800 text-red-800' : 'text-gray-600 hover:text-gray-800'}`}>Audio
                        </button>
                    </div>
                    <div className="mt-6">
                        {activeTab === 'images' && (
                            <div className="grid grid-cols-3 gap-4">
                                {results.images.length === 0 ? <p className="col-span-3 text-center text-gray-500">No
                                    images.</p> : results.images.map(item => (
                                    <div key={item.id}
                                         className="rounded overflow-hidden shadow hover:shadow-lg transition cursor-pointer"
                                         onClick={() => window.open(item.s3Link, '_blank')}>
                                        <img src={item.thumbnailLink} alt={item.id}
                                             className="w-full h-40 object-cover"/>
                                        <p className="p-2 text-sm font-medium">{item.id}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                        {activeTab === 'videos' && (
                            <div className="grid grid-cols-2 gap-6">
                                {results.videos.length === 0 ? <p className="col-span-2 text-center text-gray-500">No
                                    videos.</p> : results.videos.map(item => (
                                    <div key={item.id}
                                         className="rounded overflow-hidden shadow hover:shadow-lg transition flex flex-col"
                                         onClick={() => window.open(item.s3Link, '_blank')}>
                                        <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                                            <FiVideo size={48} className="text-gray-500"/>
                                        </div>
                                        <p className="p-2 text-sm font-medium">{item.id}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                        {activeTab === 'audio' && (
                            <div className="space-y-4">
                                {results.audio.length === 0 ?
                                    <p className="text-center text-gray-500">No audio.</p> : results.audio.map(item => (
                                        <div key={item.id}
                                             className="flex items-center bg-gray-50 rounded px-4 py-3 shadow hover:bg-gray-100 cursor-pointer"
                                             onClick={() => window.open(item.s3Link, '_blank')}>
                                            <FiVolume2 size={24} className="text-gray-600 mr-4"/>
                                            <span className="font-medium">{item.id}</span>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
