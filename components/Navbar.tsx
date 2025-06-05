"use client";

import { FiLogOut, FiUser } from "react-icons/fi";

type NavbarProps = {
  onNavigate: (path: string) => void;
  onLogout: () => void;
  username?: string;
};

export default function Navbar({ onNavigate, onLogout, username }: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center bg-white/90 backdrop-blur-md px-6 py-4 shadow-md">
      <div className="cursor-pointer flex items-center gap-2" onClick={() => onNavigate("/dashboard")}>
        <img src="/bird.png" alt="BirdTag Logo" className="w-10 h-10" />
        <h1 className="text-xl font-bold">BirdTag</h1>
      </div>
      <div className="flex gap-8 items-center">
        <button
          className="hover:text-red-800 flex items-center gap-1"
        >
          <FiUser size={18} />
          {username}
        </button>
        <button
          onClick={onLogout}
          className="hover:text-red-800 flex items-center gap-1 cursor-pointer"
        >
          <FiLogOut size={18} />
          Logout
        </button>
      </div>
    </nav>
  );
}
