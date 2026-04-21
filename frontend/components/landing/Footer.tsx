export default function Footer(): JSX.Element {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-[#0d1b2e] px-12 py-16 border-t border-white/10">
      <div className="max-w-7xl mx-auto">
        {/* 4-Column Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
          {/* Column 1: Brand */}
          <div>
            <div className="font-heading text-lg font-bold text-white mb-3">
              Tender<span className="text-amber">AI</span>
            </div>
            <p className="text-xs text-white/40 mb-4 leading-relaxed">
              Plateforme IA pour les appels d'offres. Conformité, pricing, rédaction.
            </p>
            <p className="text-xs text-white/30">
              © {currentYear} TenderAI. Tous droits réservés.
            </p>
          </div>

          {/* Column 2: Produit */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">
              Produit
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href="#features"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Fonctionnalités
                </a>
              </li>
              <li>
                <a
                  href="#pricing"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Tarifs
                </a>
              </li>
              <li>
                <a
                  href="https://docs.tenderai.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="https://api.tenderai.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  API
                </a>
              </li>
            </ul>
          </div>

          {/* Column 3: Entreprise */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">
              Entreprise
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href="/about"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  À propos
                </a>
              </li>
              <li>
                <a
                  href="/blog"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Blog
                </a>
              </li>
              <li>
                <a
                  href="/careers"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Carrières
                </a>
              </li>
              <li>
                <a
                  href="/contact"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Légal */}
          <div>
            <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">
              Légal
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href="/privacy"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Confidentialité
                </a>
              </li>
              <li>
                <a
                  href="/terms"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  CGU
                </a>
              </li>
              <li>
                <a
                  href="/legal"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Mentions légales
                </a>
              </li>
              <li>
                <a
                  href="/gdpr"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  RGPD
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Divider */}
        <div className="border-t border-white/10 pt-8">
          <p className="text-center text-xs text-white/30">
            Fabriqué avec ❤️ en Tunisie. Sécurité RGPD certifiée.
          </p>
        </div>
      </div>
    </footer>
  )
}
