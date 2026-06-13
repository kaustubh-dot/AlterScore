import { useContext } from 'react';
import { PageTransitionContext } from './transitionContext';

export default function usePageTransition() {
  const context = useContext(PageTransitionContext);
  if (!context) {
    throw new Error('usePageTransition must be used within a PageTransitionProvider');
  }
  return context;
}
