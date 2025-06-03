"use client";

import { useRouter } from "next/navigation";
import { FiLogOut, FiUpload, FiSearch, FiBell, FiUser } from "react-icons/fi";
import { FaTags } from "react-icons/fa";
import { signOut } from "@/lib/auth";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Tokens, useAuthTokens } from "@/hooks/useAuthTokens";

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
      <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center bg-white/90 backdrop-blur-md px-6 py-4 shadow-md">
        <div className="flex items-center gap-2">
          <img src="/bird.png" alt="BirdTag Logo" className="w-10 h-10" />
          <h1 className="text-xl font-bold">BirdTag</h1>
        </div>
        <div className="flex gap-8 items-center">
          <button
            onClick={() => handleNavigation("/profile")}
            className="hover:text-red-800 flex items-center gap-1 cursor-pointer"
          >
            <FiUser size={18} />
            {tokens?.name}
          </button>
          <button
            onClick={() => handleLogout()}
            className="hover:text-red-800 flex items-center gap-1 cursor-pointer"
          >
            <FiLogOut size={18} />
            Logout
          </button>
        </div>
      </nav>

      <div className="absolute inset-0 bg-white/8 z-0" />

      <main className="relative z-10 w-full max-w-4xl mx-auto p-10 rounded-xl m-auto">
        <div className="grid grid-cols-4 gap-6">
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
          <button
            onClick={() => handleNavigation("/notifications")}
            className="cursor-pointer flex flex-col items-center justify-center bg-red-800 text-white py-6 px-4 rounded-lg shadow hover:bg-red-700 transition"
          >
            <FiBell size={32} className="mb-2" />
            <span>Tag Notifications</span>
          </button>
        </div>
      </main>
    </div>
  );
}
