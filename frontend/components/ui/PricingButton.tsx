/**
 * PricingButton.tsx — Reusable CTA button with two variants
 * - 'filled': Navy background (primary action)
 * - 'outlined': Navy border (secondary action)
 * - Full-width, 48px min height
 * - Accessible focus ring, hover states
 * - Arrow animation on hover (slides in from left)
 */

import { useState } from "react";

interface PricingButtonProps {
  text: string;
  variant: 'filled' | 'outlined';
  onClick?: () => void;
  className?: string;
  featured?: boolean;
}

export default function PricingButton({
  text,
  variant,
  onClick,
  className = "",
  featured: _featured = false,
}: PricingButtonProps) {
  const [isHovered, setIsHovered] = useState(false);

  const baseStyles = [
    "w-full",
    "h-12",
    "px-6",
    "py-3",
    "text-base",
    "font-semibold",
    "rounded-lg",
    "transition-all",
    "duration-200",
    "focus:outline-none",
    "focus:ring-2",
    "focus:ring-offset-2",
    "focus:ring-amber",
    "relative",
    "overflow-hidden",
    "flex",
    "items-center",
    "justify-center",
    "gap-2",
  ];

  const variantStyles =
    variant === "filled"
      ? [
          "bg-navy",
          "text-white",
          "hover:bg-navy-light",
          "hover:scale-[1.02]",
          "active:scale-95",
        ]
      : [
          "bg-white",
          "border-2",
          "border-navy",
          "text-navy",
          "hover:bg-navy",
          "hover:text-white",
          "active:scale-95",
        ];

  const allClasses = [...baseStyles, ...variantStyles, className].join(" ");

  return (
    <button
      onClick={onClick}
      className={allClasses}
      aria-label={text}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span>{text}</span>
      
      {/* Arrow Icon - animates on hover */}
      <svg
        className={`
          w-4 h-4 transition-all duration-300
          ${isHovered ? "translate-x-0 opacity-100" : "-translate-x-3 opacity-0"}
        `}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <polyline points="5 12 19 12" />
        <polyline points="12 5 19 12 12 19" />
      </svg>
    </button>
  );
}
