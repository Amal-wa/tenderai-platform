'use client'

import { motion } from 'framer-motion'

interface PricingToggleProps {
  isAnnual: boolean
  onToggle: (isAnnual: boolean) => void
}

export default function PricingToggle({
  isAnnual,
  onToggle,
}: PricingToggleProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12 flex-wrap"
    >
      {/* Mensuel */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => onToggle(false)}
        className={`
          text-sm font-semibold transition-all duration-200 whitespace-nowrap
          ${
            !isAnnual
              ? 'text-navy'
              : 'text-muted hover:text-gray-700'
          }
        `}
      >
        Mensuel
      </motion.button>

      {/* Toggle Switch */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => onToggle(!isAnnual)}
        className={`
          relative w-14 h-8 rounded-full transition-colors duration-300 flex-shrink-0
          ${isAnnual ? 'bg-amber' : 'bg-gray-300'}
        `}
        aria-label="Toggle billing period"
      >
        <motion.div
          className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
          animate={{
            x: isAnnual ? 28 : 4,
          }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </motion.button>

      {/* Annuel with -20% badge */}
      <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap justify-center">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onToggle(true)}
          className={`
            text-sm font-semibold transition-all duration-200 whitespace-nowrap
            ${
              isAnnual
                ? 'text-navy'
                : 'text-muted hover:text-gray-700'
            }
          `}
        >
          Annuel
        </motion.button>
        {isAnnual && (
          <motion.span
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15 }}
            className="inline-block bg-amber text-white text-xs font-bold px-2.5 py-1 rounded-full whitespace-nowrap flex-shrink-0"
          >
            -20%
          </motion.span>
        )}
      </div>
    </motion.div>
  )
}
