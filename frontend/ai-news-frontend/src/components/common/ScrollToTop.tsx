import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface ScrollToTopProps {
  behavior?: ScrollBehavior;
  delay?: number;
}

/**
 * Componente que hace scroll hacia arriba cada vez que cambia la ruta
 */
const ScrollToTop: React.FC<ScrollToTopProps> = ({ 
  behavior = 'smooth',
  delay = 0 
}) => {
  const { pathname } = useLocation();

  useEffect(() => {
    const timer = setTimeout(() => {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior
      });
    }, delay);

    return () => clearTimeout(timer);
  }, [pathname, behavior, delay]);

  return null;
};

// Componente de scroll to top manual
export const ScrollToTopButton: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const toggleVisibility = () => {
      setIsVisible(window.pageYOffset > 300);
    };

    window.addEventListener('scroll', toggleVisibility);

    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  if (!isVisible) return null;

  return (
    <button
      onClick={scrollToTop}
      className="fixed bottom-8 right-8 z-50 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
      aria-label="Scroll to top"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
  );
};

export default ScrollToTop;