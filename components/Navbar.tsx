"use client";

import { FiLogOut, FiSearch, FiUpload, FiUser } from "react-icons/fi";
import NavItem from "./NavItem";
import { FaTags } from "react-icons/fa";

type NavbarProps = {
  onNavigate: (path: string) => void;
  onLogout: () => void;
  username?: string;
};

export default function Navbar({
  onNavigate,
  onLogout,
  username,
}: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center bg-white/90 backdrop-blur-md px-6 py-4 shadow-md">
      <div
        className="cursor-pointer flex items-center gap-2"
        onClick={() => onNavigate("/dashboard")}
      >
        <img src="/bird.png" alt="BirdTag Logo" className="w-10 h-10" />
        <h1 className="text-xl font-bold">BirdTag</h1>
      </div>
      <div className="flex gap-8 items-center">
        <NavItem
          label="Upload"
          icon={<FiUpload size={18} />}
          onClick={() => onNavigate("/upload")}
        />
        <NavItem
          label="Search"
          icon={<FiSearch size={18} />}
          onClick={() => onNavigate("/search")}
        />
        <NavItem
          label="Manage"
          icon={<FaTags size={18} />}
          onClick={() => onNavigate("/resource-management")}
        />
        <NavItem
          label={username || "Profile"}
          icon={<FiUser size={18} />}
          onClick={() => {}}
        />
        <NavItem
          label="Logout"
          icon={<FiLogOut size={18} />}
          onClick={onLogout}
        />
      </div>
    </nav>
  );
}
