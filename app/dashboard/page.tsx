"use client";

import { useRouter } from "next/navigation";
import { FiLogOut, FiUpload, FiSearch, FiBell, FiUser } from "react-icons/fi";
import { FaTags } from "react-icons/fa";
import { signOut } from "@/lib/auth";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Tokens, useAuthTokens } from "@/hooks/useAuthTokens";
import Navbar from "@/components/Navbar";

export default function Dashboard() {
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
    router.push("/auth/login");
  };

  return (
    <div
      className="flex flex-col min-h-screen bg-cover bg-center bg-no-repeat px-4 py-6 pt-28"
      style={{ backgroundImage: "url('/bird_picture.jpg')" }}
    >
      <Navbar
        onNavigate={handleNavigation}
        onLogout={handleLogout}
        username={tokens?.name}
      />

      <div className="absolute inset-0 bg-white/8 z-0" />

      <main className="relative z-10 w-full max-w-4xl mx-auto p-10 rounded-xl m-auto">
        <div className="grid grid-cols-3 gap-6">
          <button
            onClick={() => handleNavigation("/upload")}
            className="cursor-pointer flex flex-col items-center justify-center bg-red-800 text-white py-6 px-4 rounded-lg shadow hover:bg-red-700 transition"
          >
            <FiUpload size={32} className="mb-2" />
            <span>Upload Media</span>
          </button>
          <button
            onClick={() => handleNavigation("/search")}
            className="cursor-pointer flex flex-col items-center justify-center bg-red-800 text-white py-6 px-4 rounded-lg shadow hover:bg-red-700 transition"
          >
            <FiSearch size={32} className="mb-2" />
            <span>Query Media</span>
          </button>
          <button
            onClick={() => handleNavigation("/tags")}
            className="cursor-pointer flex flex-col items-center justify-center bg-red-800 text-white py-6 px-4 rounded-lg shadow hover:bg-red-700 transition"
          >
            <FaTags size={32} className="mb-2" />
            <span>Manage Tags</span>
          </button>
        </div>
      </main>
    </div>
  );
}
