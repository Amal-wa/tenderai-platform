import Navbar from '@/components/landing/Navbar'
import HeroSection from '@/components/landing/HeroSection'
import LogosBar from '@/components/landing/LogosBar'
import FeaturesSection from '@/components/landing/FeaturesSection'
import StatsSection from '@/components/landing/StatsSection'
import HowItWorks from '@/components/landing/HowItWorks'
import TestimonialsSection from '@/components/landing/TestimonialsSection'
import PricingSection from '@/components/landing/PricingSection'
import CtaSection from '@/components/landing/CtaSection'
import Footer from '@/components/landing/Footer'

export default function HomePage(): JSX.Element {
  return (
    <>
      <Navbar />
      <main className="pt-16">
        <HeroSection />
        <LogosBar />
        <FeaturesSection />
        <StatsSection />
        <HowItWorks />
        <TestimonialsSection />
        <PricingSection />
        <CtaSection />
        <Footer />
      </main>
    </>
  )
}
