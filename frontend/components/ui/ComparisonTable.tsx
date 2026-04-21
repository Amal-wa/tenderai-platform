/**
 * ComparisonTable.tsx — Expandable pricing feature comparison table
 * - Toggle expand/collapse with button
 * - Animated reveal with max-height transition
 * - Checkmarks and dashes for feature indicators
 */

interface ComparisonTableProps {
  isOpen: boolean;
  onToggle: () => void;
}

const comparisonData = [
  { feature: "Ingestion de documents", fondements: true, avancee: true, entreprise: true },
  { feature: "IA de rédaction", fondements: true, avancee: true, entreprise: true },
  { feature: "Matrice de conformité", fondements: false, avancee: true, entreprise: true },
  { feature: "Moteur de pricing", fondements: false, avancee: true, entreprise: true },
  { feature: "Agent proactif", fondements: false, avancee: true, entreprise: true },
  { feature: "Intégrations CRM/ERP", fondements: false, avancee: true, entreprise: true },
  { feature: "Simulation Monte-Carlo", fondements: false, avancee: false, entreprise: true },
  { feature: "Auto-soumission portails", fondements: false, avancee: false, entreprise: true },
  { feature: "Hébergement souverain", fondements: false, avancee: false, entreprise: true },
  { feature: "Support 24/7 + SLA", fondements: false, avancee: false, entreprise: true },
];

const CheckMark = () => (
  <svg
    className="w-5 h-5 text-amber mx-auto inline"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const Dash = () => (
  <span className="text-gray-400 font-semibold text-lg">—</span>
);

export default function ComparisonTable({
  isOpen,
  onToggle,
}: ComparisonTableProps) {
  return (
    <div className="max-w-6xl mx-auto mt-12">
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="
          mx-auto block py-3 px-6 rounded-lg border border-cream
          bg-white text-navy font-semibold text-sm
          hover:bg-cream transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-amber
        "
      >
        {isOpen
          ? "Masquer la comparaison ↑"
          : "Comparer tous les plans ↓"}
      </button>

      {/* Table Container with Animation */}
      <div
        className={`
          overflow-hidden transition-all duration-500 ease-in-out
          ${isOpen ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"}
        `}
      >
        <div className="mt-6 rounded-2xl overflow-hidden border border-cream-border shadow-subtle">
          <table className="w-full">
            {/* Header */}
            <thead>
              <tr className="bg-navy text-white">
                <th className="px-6 py-4 text-left text-sm font-semibold">
                  Fonctionnalité
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold">
                  Fondements
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold border-t-2 border-amber">
                  Version avancée
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold">
                  Entreprise
                </th>
              </tr>
            </thead>

            {/* Body */}
            <tbody className="divide-y divide-cream-border">
              {comparisonData.map((row, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-cream"}>
                  <td className="px-6 py-4 text-sm font-medium text-navy">
                    {row.feature}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {row.fondements ? <CheckMark /> : <Dash />}
                  </td>
                  <td className="px-6 py-4 text-center border-t-2 border-amber border-opacity-30">
                    {row.avancee ? <CheckMark /> : <Dash />}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {row.entreprise ? <CheckMark /> : <Dash />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
