/**
 * FeatureItem.tsx — Reusable feature list item with amber checkmark
 * - Inline SVG checkmark (no external icon library)
 * - RTL-safe layout with gap-x-3 and items-start
 * - Accessible semantic markup
 */

interface FeatureItemProps {
  text: string;
  className?: string;
}

export default function FeatureItem({ text, className = "" }: FeatureItemProps) {
  return (
    <div className={`flex items-start gap-x-3 text-sm leading-relaxed ${className}`}>
      {/* Inline SVG Checkmark */}
      <svg
        className="w-5 h-5 text-amber flex-shrink-0 mt-0.5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <polyline points="20 6 9 17 4 12" />
      </svg>
      
      {/* Feature Text */}
      <span className="text-gray-700">{text}</span>
    </div>
  );
}
