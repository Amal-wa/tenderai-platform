/**
 * PricingCard.tsx — Enhanced pricing plan card with categories, dynamic pricing, social proof
 * - Props-driven configuration with dynamic prices
 * - Grouped feature categories with expand/collapse
 * - Featured variant: navy bg with white text + amber price
 * - Social proof line under CTA
 * - Accessibility: role="article", aria-label on CTA
 * - RTL-compatible
 */

import { useState } from "react";
import PricingButton from "./PricingButton";

interface FeatureCategory {
  label: string;
  items: string[];
}

interface PricingCardProps {
  title: string;
  description: string;
  price: string | number;
  annualPrice?: string | number;
  isAnnual?: boolean;
  unit?: string;
  featureCategories?: FeatureCategory[];
  cta: string;
  ctaVariant: "filled" | "outlined";
  featured?: boolean;
  badge?: string;
  socialProof?: string;
  className?: string;
  // Enterprise-specific
  enterpriseStartPrice?: number;
}

export default function PricingCard({
  title,
  description,
  price,
  annualPrice,
  isAnnual = false,
  unit = "TND/mois",
  featureCategories = [],
  cta,
  ctaVariant,
  featured = false,
  badge,
  socialProof,
  className = "",
  enterpriseStartPrice,
}: PricingCardProps) {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(
    featureCategories.length > 0 ? featureCategories[0].label : null
  );

  // Determine which price to display
  const displayPrice = isAnnual && annualPrice ? annualPrice : price;
  const priceClassName = featured ? "text-amber" : "text-navy";

  // Animation class for price transitions
  const currentPrice = String(displayPrice);

  return (
    <div
      role="article"
      className={`
        relative
        rounded-2xl
        p-8
        transition-all
        duration-300
        ${
          featured
            ? "bg-navy text-white border-2 border-amber shadow-[0_20px_60px_rgba(196,150,42,0.2)] md:scale-105"
            : "bg-white text-navy border border-cream shadow-subtle"
        }
        ${className}
      `}
    >
      {/* Badge (for featured card) */}
      {featured && badge && (
        <div
          className="
            absolute
            -top-4
            left-1/2
            -translate-x-1/2
            bg-amber
            text-navy
            px-4
            py-1.5
            rounded-full
            text-xs
            font-semibold
            whitespace-nowrap
          "
        >
          {badge}
        </div>
      )}

      {/* Title */}
      <h3
        className={`
          text-xl
          font-semibold
          mb-3
          leading-snug
          ${featured ? "text-white" : "text-navy"}
        `}
      >
        {title}
      </h3>

      {/* Description */}
      <p className={`text-sm mb-7 leading-relaxed ${featured ? "text-gray-200" : "text-gray-600"}`}>
        {description}
      </p>

      {/* Price with animation */}
      <div className="mb-8 overflow-hidden">
        <div
          className="transition-all duration-300"
          key={currentPrice}
        >
          <span className={`text-5xl font-bold ${priceClassName} block`}>
            {displayPrice}
          </span>
          {enterpriseStartPrice && (
            <p className={`text-xs mt-1 ${featured ? "text-gray-300" : "text-muted"}`}>
              Prix de départ · Sur devis selon périmètre
            </p>
          )}
          {!enterpriseStartPrice && (
            <span className={`text-sm ml-2 ${featured ? "text-gray-300" : "text-gray-500"}`}>
              {unit}
            </span>
          )}
        </div>
      </div>

      {/* Feature Categories */}
      {featureCategories.length > 0 && (
        <div className="mb-8 space-y-4">
          {featureCategories.map((category) => (
            <div key={category.label}>
              {/* Category Header - Toggle */}
              <button
                onClick={() =>
                  setExpandedCategory(
                    expandedCategory === category.label ? null : category.label
                  )
                }
                className={`
                  w-full flex items-center justify-between py-2 px-3
                  rounded-lg transition-colors duration-200
                  ${
                    expandedCategory === category.label
                      ? featured
                        ? "bg-white bg-opacity-10"
                        : "bg-cream"
                      : "hover:bg-opacity-5"
                  }
                `}
              >
                <span
                  className={`
                    text-xs font-semibold uppercase tracking-wide
                    ${featured ? "text-amber" : "text-muted"}
                  `}
                >
                  {category.label}
                </span>
                <svg
                  className={`
                    w-4 h-4 transition-transform duration-300
                    ${expandedCategory === category.label ? "rotate-180" : ""}
                    ${featured ? "text-amber" : "text-muted"}
                  `}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {/* Features List - Expandable */}
              {expandedCategory === category.label && (
                <div className="mt-3 space-y-2 pl-3 border-l-2 border-opacity-20 border-amber">
                  {category.items.map((feature, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-sm animate-fadeIn"
                    >
                      {/* Checkmark */}
                      <svg
                        className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                          featured ? "text-amber" : "text-amber"
                        }`}
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
                      <span className={featured ? "text-gray-100" : "text-gray-700"}>
                        {feature}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* CTA Button */}
      <div className="mb-3">
        <PricingButton
          text={cta}
          variant={ctaVariant}
          featured={featured}
          onClick={() => console.log(`CTA clicked: ${cta}`)}
        />
      </div>

      {/* Social Proof */}
      {socialProof && (
        <p
          className={`
            text-xs text-center
            ${featured ? "text-gray-300" : "text-muted"}
          `}
        >
          {socialProof}
        </p>
      )}
    </div>
  );
}
