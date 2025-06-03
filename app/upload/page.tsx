'use client';

import { useState } from "react";
import { FiUpload } from "react-icons/fi";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("");

    if (!file) {
      setStatus("Please select a file.");
      return;
    }

    setLoading(true);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setStatus("File upload simulated successfully!");
    setFile(null);
    setLoading(false);
  };

  return (
    <div
      className="flex items-center justify-center min-h-screen bg-gray-100 px-4 bg-no-repeat bg-cover bg-center"
      style={{ backgroundImage: "url('/bird_picture.jpg')" }}
    >
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
    <p className="text-sm text-center mt-4 text-gray-700">{status}</p>
  )}
</div>

      </form>
    </div>
  );
}
