import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSound from './useSound';
import PageCurtain from '../components/animation/PageCurtain';
import { PageTransitionContext } from './transitionContext';
import { prefersReducedMotion } from '../lib/motionPreferences';

export function PageTransitionProvider({ children }) {
  const navigate = useNavigate();
  const { playTransition } = useSound();
  const [curtainState, setCurtainState] = useState('idle'); // 'idle' | 'in' | 'out'
  const timersRef = useRef([]);

  useEffect(() => () => {
    timersRef.current.forEach(window.clearTimeout);
  }, []);

  const transitionTo = (path, stateOptions = {}) => {
    if (curtainState !== 'idle') return;

    if (prefersReducedMotion()) {
      navigate(path, stateOptions);
      return;
    }

    // Play noise sweep sound
    playTransition();
    setCurtainState('in');

    // Wait for curtain to cover screen (500ms duration)
    timersRef.current.push(window.setTimeout(() => {
      navigate(path, stateOptions);
      
      // Hold closed for 150ms to let the new page fully mount
      timersRef.current.push(window.setTimeout(() => {
        setCurtainState('out');

        // Wait for curtain to clear (500ms duration)
        timersRef.current.push(window.setTimeout(() => {
          setCurtainState('idle');
          timersRef.current = [];
        }, 500));
      }, 150));
    }, 500));
  };

  return (
    <PageTransitionContext.Provider value={{ curtainState, transitionTo }}>
      {children}
      <PageCurtain state={curtainState} />
    </PageTransitionContext.Provider>
  );
}
