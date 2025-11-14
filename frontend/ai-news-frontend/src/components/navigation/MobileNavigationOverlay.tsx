import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

interface MobileNavigationOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

/**
 * Componente para overlay de navegación móvil
 * Se renderiza en un portal para aparecer sobre todo el contenido
 */
const MobileNavigationOverlay: React.FC<MobileNavigationOverlayProps> = ({
  isOpen,
  onClose,
  children,
  className = ''
}) => {
  // Prevenir scroll del body cuando el overlay está abierto
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Manejar tecla ESC para cerrar
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const overlay = (
    <div 
      className={`
        fixed inset-0 z-50 bg-black bg-opacity-50 backdrop-blur-sm
        animate-in fade-in duration-200
        ${className}
      `}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-hidden="true"
    >
      <div 
        className="
          h-full w-full max-w-sm ml-auto
          bg-white shadow-2xl
          transform transition-transform duration-300 ease-in-out
          animate-in slide-in-from-right
        "
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );

  return createPortal(overlay, document.body);
};

export default MobileNavigationOverlay;