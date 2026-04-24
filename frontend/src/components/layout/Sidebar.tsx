"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Search,
  Map,
  MessageSquare,
  Megaphone,
  Phone,
  Settings,
  Radar,
  Inbox,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/leads", label: "Leads / CRM", icon: Users },
  { href: "/scrape", label: "Prospection", icon: Search },
  { href: "/map", label: "Carte", icon: Map },
  { href: "/campaigns", label: "Campagnes", icon: Megaphone },
  { href: "/messages", label: "Messages", icon: MessageSquare },
  { href: "/messages/inbox", label: "Boîte de réception", icon: Inbox, indent: true },
  { href: "/voip", label: "Appels", icon: Phone },
  { href: "/settings", label: "Paramètres", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-full shrink-0">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-800">
        <Radar className="text-blue-400" size={24} />
        <span className="text-lg font-bold tracking-tight">HGI Radar</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon, indent }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-lg text-sm font-medium transition-colors",
              indent ? "px-3 py-2 ml-4" : "px-3 py-2.5",
              pathname === href
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            )}
          >
            <Icon size={indent ? 15 : 18} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-500 text-center">HGI Radar v1.0</p>
      </div>
    </aside>
  );
}
