import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSound from './useSound';
import PageCurtain from '../components/animation/PageCurtain';
import { PageTransitionContext } from './transitionContext';
import { prefersReducedMotion } from '../lib/motionPreferences';

const CURTAIN_IN_MS = 260;
const CURTAIN_HOLD_MS = 60;
const CURTAIN_OUT_MS = 300;

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

    // Keep route changes legible without making navigation feel blocked.
    timersRef.current.push(window.setTimeout(() => {
      navigate(path, stateOptions);
      
      timersRef.current.push(window.setTimeout(() => {
        setCurtainState('out');

        timersRef.current.push(window.setTimeout(() => {
          setCurtainState('idle');
          timersRef.current = [];
        }, CURTAIN_OUT_MS));
      }, CURTAIN_HOLD_MS));
    }, CURTAIN_IN_MS));
  };

  return (
    <PageTransitionContext.Provider value={{ curtainState, transitionTo }}>
      {children}
      <PageCurtain state={curtainState} />
    </PageTransitionContext.Provider>
  );
}
