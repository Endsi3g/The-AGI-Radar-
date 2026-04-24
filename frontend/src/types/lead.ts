export type LeadStatus = "nouveau" | "contacté" | "réponse" | "rdv" | "fermé" | "perdu";

export interface Lead {
  id: string;
  business_name: string;
  industry: string | null;
  description: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  city: string | null;
  province: string;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  google_place_id: string | null;
  google_rating: number | null;
  google_reviews: number | null;
  yelp_url: string | null;
  linkedin_url: string | null;
  instagram_handle: string | null;
  facebook_url: string | null;
  owner_name: string | null;
  owner_title: string | null;
  owner_linkedin: string | null;
  detected_language: string;
  status: LeadStatus;
  ai_score: number | null;
  score_rationale: string | null;
  source_flags: string[];
  assigned_to: string | null;
  last_contacted_at: string | null;
  next_followup_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Interaction {
  id: string;
  type: string;
  notes: string | null;
  metadata: Record<string, unknown> | null;
  occurred_at: string;
}

export const STATUS_LABELS: Record<LeadStatus, string> = {
  nouveau: "Nouveau",
  contacté: "Contacté",
  réponse: "Réponse",
  rdv: "RDV",
  fermé: "Fermé",
  perdu: "Perdu",
};

export const STATUS_COLORS: Record<LeadStatus, string> = {
  nouveau: "bg-blue-100 text-blue-700 border-blue-200",
  contacté: "bg-amber-100 text-amber-700 border-amber-200",
  réponse: "bg-emerald-100 text-emerald-700 border-emerald-200",
  rdv: "bg-violet-100 text-violet-700 border-violet-200",
  fermé: "bg-gray-100 text-gray-600 border-gray-200",
  perdu: "bg-red-100 text-red-600 border-red-200",
};

export const STATUS_DOT: Record<LeadStatus, string> = {
  nouveau: "bg-blue-500",
  contacté: "bg-amber-500",
  réponse: "bg-emerald-500",
  rdv: "bg-violet-500",
  fermé: "bg-gray-400",
  perdu: "bg-red-500",
};

export const PIPELINE_COLUMNS: LeadStatus[] = [
  "nouveau",
  "contacté",
  "réponse",
  "rdv",
  "fermé",
  "perdu",
];

export const INDUSTRY_LABELS: Record<string, string> = {
  restaurant: "Restaurant",
  cafe: "Café",
  hotel: "Hôtel",
  plombier: "Plombier",
  electricien: "Électricien",
  serrurier: "Serrurier",
  peintre: "Peintre",
  menuisier: "Menuisier",
  autre: "Autre",
};

export const SOURCE_ICONS: Record<string, string> = {
  google_maps: "🗺️",
  pages_jaunes: "📒",
  yelp: "⭐",
  linkedin: "💼",
  instagram: "📸",
  facebook: "👥",
};
