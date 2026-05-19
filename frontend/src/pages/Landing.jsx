import Footer from "../components/footer/Footer.jsx";
import HeroSection from "../components/hero/HeroSection.jsx";
import ManifestoSection from "../components/manifesto/ManifestoSection.jsx";
import PillarsSection from "../components/pillars/PillarsSection.jsx";

export default function Landing() {
  return (
    <main className="landing-page">
      <HeroSection />
      <ManifestoSection />
      <PillarsSection />
      <Footer />
    </main>
  );
}
