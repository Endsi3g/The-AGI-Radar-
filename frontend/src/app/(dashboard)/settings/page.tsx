import Link from "next/link";
import { Plug, Users, ChevronRight } from "lucide-react";

const SECTIONS = [
  {
    href: "/settings/integrations",
    icon: Plug,
    title: "Intégrations",
    description: "Connectez Google (Gmail, Calendar) et Twilio",
    color: "bg-blue-50 text-blue-600",
  },
  {
    href: "/settings/team",
    icon: Users,
    title: "Équipe",
    description: "Gérer les membres et leurs rôles",
    color: "bg-violet-50 text-violet-600",
  },
];

export default function SettingsPage() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Paramètres</h1>
        <p className="text-sm text-gray-500 mt-1">Configuration de votre espace HGI Radar</p>
      </div>

      <div className="space-y-3">
        {SECTIONS.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="flex items-center gap-4 bg-white border border-gray-200 rounded-2xl px-5 py-4 hover:shadow-sm transition-shadow group"
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${s.color}`}>
              <s.icon size={18} />
            </div>
            <div className="flex-1">
              <p className="font-medium text-gray-900">{s.title}</p>
              <p className="text-sm text-gray-500">{s.description}</p>
            </div>
            <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-400 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
