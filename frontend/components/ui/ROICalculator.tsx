/**
 * ROICalculator.tsx — Interactive ROI slider + animated metrics
 * - Slider: 1–50 AOs/mois
 * - Animated count-up effect on value change
 * - Shows savings in hours and money
 */

import { useState, useEffect } from "react";

interface ROICalculatorProps {
  className?: string;
}

export default function ROICalculator({ className = "" }: ROICalculatorProps) {
  const [aoCount, setAoCount] = useState(5);
  const [displayedHours, setDisplayedHours] = useState(0);
  const [displayedMoney, setDisplayedMoney] = useState(0);

  const hoursPerAO = 8;
  const hourlyRate = 25; // TND
  const savingsPercentage = 0.7; // 70% time saved

  const actualHours = Math.round(aoCount * hoursPerAO * savingsPercentage);
  const actualMoney = Math.round(actualHours * hourlyRate);

  // Animate numbers when they change
  useEffect(() => {
    let animationId: number;
    let currentHours = displayedHours;
    let currentMoney = displayedMoney;
    const increment = Math.max(1, Math.ceil((actualHours - displayedHours) / 20));
    const moneyIncrement = Math.max(1, Math.ceil((actualMoney - displayedMoney) / 20));

    const animate = () => {
      if (currentHours < actualHours) {
        currentHours = Math.min(currentHours + increment, actualHours);
        setDisplayedHours(currentHours);
      }
      if (currentMoney < actualMoney) {
        currentMoney = Math.min(currentMoney + moneyIncrement, actualMoney);
        setDisplayedMoney(currentMoney);
      }

      if (currentHours < actualHours || currentMoney < actualMoney) {
        animationId = requestAnimationFrame(animate);
      }
    };

    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, [aoCount, actualHours, actualMoney]);

  return (
    <div className={`mx-auto max-w-6xl mb-16 ${className}`}>
      <div className="bg-white rounded-2xl p-12 border border-cream-border shadow-subtle">
        {/* Title */}
        <h3 className="text-2xl font-bold text-navy text-center mb-8">
          Calculez votre retour sur investissement
        </h3>

        {/* Slider */}
        <div className="mb-12 px-4">
          <div className="flex items-center justify-between mb-4">
            <label className="text-sm font-semibold text-muted">
              Appels d'offres par mois
            </label>
            <span className="text-2xl font-bold text-amber">
              {aoCount}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="50"
            value={aoCount}
            onChange={(e) => setAoCount(parseInt(e.target.value))}
            className="w-full h-2 bg-cream-border rounded-lg appearance-none cursor-pointer 
              [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 
              [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full 
              [&::-webkit-slider-thumb]:bg-amber [&::-webkit-slider-thumb]:cursor-pointer
              [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 
              [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-amber
              [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0"
            aria-label="Number of tenders per month"
          />
          <div className="flex justify-between text-xs text-muted mt-2">
            <span>1</span>
            <span>50</span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          {/* Hours Saved */}
          <div className="text-center p-6 rounded-xl" style={{ backgroundColor: "rgba(196, 150, 42, 0.12)" }}>
            <p className="text-sm text-muted mb-2">Économisées par mois</p>
            <p className="text-4xl font-bold text-amber">
              {displayedHours}
              <span className="text-2xl ml-1">h</span>
            </p>
          </div>

          {/* Money Saved */}
          <div className="text-center p-6 rounded-xl" style={{ backgroundColor: "rgba(19, 32, 58, 0.05)" }}>
            <p className="text-sm text-muted mb-2">Économisés par mois</p>
            <p className="text-4xl font-bold text-navy">
              {displayedMoney}
              <span className="text-2xl ml-1">TND</span>
            </p>
          </div>
        </div>

        {/* Subtitle */}
        <p className="text-xs text-muted text-center">
          Basé sur 8h de traitement manuel par AO · Taux horaire moyen 25 TND
        </p>
      </div>
    </div>
  );
}
