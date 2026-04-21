'use client'

export interface Step {
  id: string
  label: string
  number: number
}

export interface StepIndicatorProps {
  steps: Step[]
  currentStep: string
}

export default function StepIndicator({
  steps,
  currentStep,
}: StepIndicatorProps): JSX.Element {
  const currentIndex = steps.findIndex((s) => s.id === currentStep)

  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {steps.map((step, idx) => {
        const isActive = step.id === currentStep
        const isDone = idx < currentIndex
        const isNext = idx > currentIndex

        return (
          <div key={step.id} className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              {/* Circle */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-heading font-bold transition-all ${
                  isDone
                    ? 'bg-amber text-white'
                    : isActive
                      ? 'bg-amber text-white ring-2 ring-amber ring-offset-2'
                      : 'bg-cream border-2 border-cream-border text-muted'
                }`}
              >
                {isDone ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  step.number
                )}
              </div>

              {/* Label */}
              <span
                className={`text-xs font-medium mt-2 ${
                  isActive ? 'text-navy' : isNext ? 'text-muted' : 'text-amber'
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector */}
            {idx < steps.length - 1 && (
              <div
                className={`w-12 h-1 mx-2 rounded-full transition-all ${
                  isDone ? 'bg-amber' : 'bg-cream-border'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
