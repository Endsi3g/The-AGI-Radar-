"use client";

import { Bell, LogOut } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import { useRouter } from "next/navigation";

export function TopBar() {
  const { clearTokens } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <header className="h-14 bg-white border-b flex items-center justify-between px-6 shrink-0">
      <div />
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <Bell size={18} className="text-gray-600" />
        </button>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          Déconnexion
        </button>
      </div>
    </header>
  );
}
