'use client';


import { useState } from "react";
import { FiUpload } from "react-icons/fi";
import { useCurrentUser } from '@/hooks/useCurrentUser';
import Navbar from "@/components/Navbar";
import { useRouter } from "next/navigation";
import { useAuthTokens, Tokens } from "@/hooks/useAuthTokens";
import { signOut } from "@/lib/auth";



export default function UploadPage() {
  
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const tokens: Tokens = useAuthTokens();
  

  const { checking } = useCurrentUser();
  
  if (checking)
    return (
      <div>
        <h1 className="text-center text-2xl font-bold mt-20">
          Checking Session...
        </h1>
      </div>
    );


  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const handleLogout = () => {
    signOut();
    router.push('/auth/login');
  };
  

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setStatus("");

  if (!file) {
    setStatus("Please select a file.");
    return;
  }

  setLoading(true);

  try {
    const base64 = await toBase64(file);
    const fileName = file.name;

    try {
  const res = await fetch("https://obadhri1sg.execute-api.us-east-1.amazonaws.com/prod/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file: base64, fileName }),
  });

  const text = await res.text();
  if (!res.ok) throw new Error(`API ${res.status}: ${text}`);
  setStatus("Upload successful!");
  setFile(null);

} catch (err: any) {
  console.error(err);
  setStatus("Upload failed: " + err.message);
}
  } catch (err: any) {
    console.error(err);
    setStatus("Upload failed: " + err.message);
  }

  setLoading(false);
};

const toBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
  });
};

  return (
    <div
      className="flex items-center justify-center min-h-screen bg-gray-100 px-4 bg-no-repeat bg-cover bg-center"
      style={{ backgroundImage: "url('/bird_picture.jpg')" }}
    >
      <Navbar
        onNavigate={handleNavigation}
        onLogout={handleLogout}
        username={tokens?.name}
      />
      <form
        onSubmit={handleSubmit}
        className="relative z-10 w-full max-w-sm rounded-lg bg-white/90 p-8 shadow-xl backdrop-blur"
      >
        <div className="flex flex-row items-center justify-center mb-6 gap-2">
          <div className="text-center">
            <img
              src="/bird.png"
              alt="BirdTag Logo"
              className="mx-auto mb-4 w-16 h-16"
            />
          </div>
          <h1 className="text-2xl font-bold text-center mb-6">BirdTag</h1>
        </div>

        <div className="space-y-4">
  <label
    htmlFor="file-upload"
    className="flex items-center justify-between cursor-pointer w-full border border-gray-300 px-4 py-3 rounded-lg bg-white hover:bg-gray-50 transition"
  >
    <span className="text-gray-600 truncate">
      {file ? file.name : "Choose a file to upload"}
    </span>
    <FiUpload className="text-red-800" />
    <input
      id="file-upload"
      type="file"
      accept="image/*,audio/*,video/*"
      onChange={(e) => setFile(e.target.files?.[0] || null)}
      className="hidden"
    />
  </label>

  <button
    type="submit"
    disabled={loading}
    className={`flex items-center justify-center gap-2 w-full ${
      loading ? "bg-red-400" : "bg-red-800"
    } text-white font-semibold py-3 px-4 rounded-lg`}
  >
    <FiUpload size={20} />
    {loading ? "Uploading..." : "Upload File"}
  </button>

  {status && (
  <p
    className={`text-sm text-center mt-4 font-medium ${
      status.toLowerCase().includes("success")
        ? "text-green-700"
        : "text-red-600"
    }`}
  >
    {status}
  </p>
)}
</div>

      </form>
    </div>
  );
}
