export default function Loading() {
  return (
    <div className="p-8 space-y-6 animate-pulse">
      <div className="h-48 rounded-2xl bg-[var(--navy)] opacity-20" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-36 rounded-2xl bg-white border border-[var(--cream-3)]" />
        ))}
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-36 rounded-2xl bg-white border border-[var(--cream-3)]" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-36 rounded-2xl bg-white border border-[var(--cream-3)]" />
        ))}
      </div>
    </div>
  )
}
