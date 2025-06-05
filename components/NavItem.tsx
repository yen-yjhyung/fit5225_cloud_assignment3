"use client";

import { ReactNode } from "react";

type NavItemProps = {
  label: string;
  icon: ReactNode;
  onClick: () => void;
};

export default function NavItem({ label, icon, onClick }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className="hover:text-red-800 flex items-center gap-1 cursor-pointer"
    >
      {icon}
      {label}
    </button>
  );
}
