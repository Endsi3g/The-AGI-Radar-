export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Nouveaux leads", value: "—", color: "bg-blue-500" },
          { label: "Contactés", value: "—", color: "bg-amber-500" },
          { label: "Réponses reçues", value: "—", color: "bg-emerald-500" },
          { label: "RDV planifiés", value: "—", color: "bg-violet-500" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl shadow-sm border p-5">
            <div className={`w-3 h-3 rounded-full ${stat.color} mb-3`} />
            <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <p className="text-gray-500 text-center py-8">
          Les statistiques apparaîtront ici une fois les données chargées.
        </p>
      </div>
    </div>
  );
}
