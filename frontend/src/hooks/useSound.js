import { useEffect, useRef, useState } from 'react';

// Singleton state to persist background classical pad loop across components/renders
let ambientInterval = null;
let currentPieceIndex = Math.floor(Math.random() * 6);
let currentMeasureIndex = 0;
let soundMuted = localStorage.getItem('alterscore_sound_muted') === 'true';

const notifySoundPreference = () => {
  window.dispatchEvent(new CustomEvent('alterscore_sound_muted_change', { detail: soundMuted }));
};

const stopAmbient = () => {
  if (ambientInterval) {
    clearInterval(ambientInterval);
    ambientInterval = null;
  }
};

const startAmbient = (ctx) => {
  if (ambientInterval) return; // Already running

  const pieces = [
    {
      name: "Beethoven - Moonlight Sonata (Adagio Sostenuto)",
      type: "moonlight",
      measureDuration: 4200,
      measures: [
        { bass: 73.42, triplet: [207.65, 277.18, 329.63] }, // C#2, [G#3, C#4, E4]
        { bass: 61.74, triplet: [207.65, 277.18, 329.63] }, // B2, [G#3, C#4, E4]
        { bass: 55.00, triplet: [220.00, 277.18, 369.99] }, // A2, [A3, C#4, F#4]
        { bass: 46.25, triplet: [220.00, 293.66, 369.99] }, // F#2, [A3, D4, F#4]
        { bass: 51.91, triplet: [207.65, 261.63, 311.13] }, // G#2, [G#3, C4, D#4]
        { bass: 73.42, triplet: [207.65, 277.18, 329.63] }, // C#2, [G#3, C#4, E4]
        { bass: 51.91, triplet: [207.65, 261.63, 311.13] }, // G#2, [G#3, C4, D#4]
        { bass: 73.42, triplet: [207.65, 277.18, 329.63] }  // C#2, [G#3, C#4, E4]
      ]
    },
    {
      name: "Chopin - Prelude in E Minor (Op. 28 No. 4)",
      type: "chopin_prelude",
      measureDuration: 4500,
      measures: [
        { bass: 82.41, chord: [196.00, 246.94, 329.63], melody: 493.88 }, // E2, [G3, B3, E4], B4
        { bass: 82.41, chord: [185.00, 233.08, 329.63], melody: 523.25 }, // E2, [F#3, A#3, E4], C5
        { bass: 73.42, chord: [174.61, 220.00, 329.63], melody: 493.88 }, // D2, [F3, A3, E4], B4
        { bass: 73.42, chord: [164.81, 207.65, 311.13], melody: 466.16 }, // D2, [E3, G#3, D#4], Bb4
        { bass: 65.41, chord: [164.81, 196.00, 293.66], melody: 440.00 }, // C2, [E3, G3, D4], A4
        { bass: 65.41, chord: [155.56, 185.00, 261.63], melody: 392.00 }, // C2, [Eb3, Gb3, C4], G4
        { bass: 55.00, chord: [146.83, 185.00, 261.63], melody: 369.99 }, // A1, [D3, F#3, C4], F#4
        { bass: 55.00, chord: [138.59, 164.81, 233.08], melody: 329.63 }  // A1, [C#3, E3, A#3], E4
      ]
    },
    {
      name: "Albinoni - Adagio in G Minor",
      type: "albinoni",
      measureDuration: 4200,
      measures: [
        { bass: 98.00, chord: [196.00, 233.08, 293.66], melody: 392.00 }, // G2, [G3, Bb3, D4], G4
        { bass: 87.31, chord: [220.00, 261.63, 349.23], melody: 440.00 }, // F2, [A3, C4, F4], A4
        { bass: 77.78, chord: [196.00, 233.08, 311.13], melody: 466.16 }, // Eb2, [G3, Bb3, Eb4], Bb4
        { bass: 73.42, chord: [185.00, 220.00, 293.66], melody: 554.37 }, // D2, [F#3, A3, D4], C#5
        { bass: 65.41, chord: [196.00, 261.63, 311.13], melody: 587.33 }, // C2, [G3, C4, Eb4], D5
        { bass: 58.27, chord: [174.61, 233.08, 293.66], melody: 523.25 }, // Bb1, [F3, Bb3, D4], C5
        { bass: 55.00, chord: [164.81, 220.00, 277.18], melody: 466.16 }, // A1, [E3, A3, C#4], Bb4
        { bass: 73.42, chord: [185.00, 220.00, 293.66], melody: 440.00 }  // D2, [F#3, A3, D4], A4
      ]
    },
    {
      name: "Chopin - Funeral March",
      type: "funeral",
      measureDuration: 4000,
      measures: [
        { bass: 58.27, chord: [138.59, 174.61, 233.08], melody: 466.16 }, // Bb1, [Db3, F3, Bb3], Bb4
        { bass: 58.27, chord: [138.59, 174.61, 233.08], melody: 466.16 }, // Bb1, [Db3, F3, Bb3], Bb4
        { bass: 46.25, chord: [138.59, 174.61, 277.18], melody: 554.37 }, // Gb1, [Db3, F3, Db4], Db5
        { bass: 43.65, chord: [130.81, 164.81, 261.63], melody: 523.25 }, // F1, [C3, E3, C4], C5
        { bass: 58.27, chord: [138.59, 174.61, 233.08], melody: 466.16 }, // Bb1, [Db3, F3, Bb3], Bb4
        { bass: 58.27, chord: [138.59, 174.61, 233.08], melody: 466.16 }, // Bb1, [Db3, F3, Bb3], Bb4
        { bass: 46.25, chord: [138.59, 174.61, 277.18], melody: 554.37 }, // Gb1, [Db3, F3, Db4], Db5
        { bass: 43.65, chord: [130.81, 164.81, 261.63], melody: 523.25 }  // F1, [C3, E3, C4], C5
      ]
    },
    {
      name: "Tchaikovsky - Pathetique Symphony (IV. Adagio Lamentoso)",
      type: "pathetique",
      measureDuration: 4600,
      measures: [
        { bass: 61.74, chord: [293.66, 369.99], melody: 493.88 }, // B1, [D4, F#4], B4
        { bass: 51.91, chord: [293.66, 329.63], melody: 440.00 }, // G#1, [D4, E4], A4
        { bass: 55.00, chord: [277.18, 329.63], melody: 440.00 }, // A1, [C#4, E4], A4
        { bass: 46.25, chord: [277.18, 293.66], melody: 392.00 }, // F#1, [C#4, D4], G4
        { bass: 49.00, chord: [246.94, 293.66], melody: 392.00 }, // G1, [B3, D4], G4
        { bass: 41.20, chord: [246.94, 277.18], melody: 349.23 }, // E1, [B3, C#4], F4
        { bass: 46.25, chord: [233.08, 277.18], melody: 369.99 }, // F#1, [A#3, C#4], F#4
        { bass: 61.74, chord: [246.94, 293.66], melody: 246.94 }  // B1, [B3, D4], B3
      ]
    },
    {
      name: "Barber - Adagio for Strings",
      type: "barber",
      measureDuration: 4800,
      measures: [
        { bass: 58.27, chord: [233.08, 277.18, 349.23], melody: 349.23 }, // Bb1, [Bb3, Db4, F4], F4
        { bass: 69.30, chord: [233.08, 277.18, 369.99], melody: 369.99 }, // Db2, [Bb3, Db4, Gb4], Gb4
        { bass: 77.78, chord: [277.18, 349.23, 415.30], melody: 415.30 }, // Eb2, [Db4, F4, Ab4], Ab4
        { bass: 87.31, chord: [311.13, 349.23, 466.16], melody: 466.16 }, // F2, [Eb4, F4, Bb4], Bb4
        { bass: 87.31, chord: [349.23, 415.30, 523.25], melody: 523.25 }, // F2, [F4, Ab4, C5], C5
        { bass: 77.78, chord: [311.13, 349.23, 466.16], melody: 466.16 }, // Eb2, [Eb4, F4, Bb4], Bb4
        { bass: 69.30, chord: [277.18, 349.23, 415.30], melody: 415.30 }, // Db2, [Db4, F4, Ab4], Ab4
        { bass: 58.27, chord: [233.08, 277.18, 349.23], melody: 349.23 }  // Bb1, [Bb3, Db4, F4], F4
      ]
    }
  ];

  const playNote = (freq, time, instrument = 'string', duration = 3.5, volume = 0.015) => {
    try {
      const gainNode = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      filter.type = 'lowpass';
      filter.connect(gainNode);
      gainNode.connect(ctx.destination);

      if (instrument === 'string') {
        // Detuned string ensemble layers (rich chorus feel)
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();

        osc1.type = 'triangle';
        osc2.type = 'triangle';

        osc1.frequency.setValueAtTime(freq, time);
        osc1.detune.setValueAtTime(5, time); // detuned slightly up

        osc2.frequency.setValueAtTime(freq, time);
        osc2.detune.setValueAtTime(-5, time); // detuned slightly down

        // Tragic Vibrato (4.2 Hz, human violin pitch modulation)
        const lfo = ctx.createOscillator();
        const lfoGain = ctx.createGain();
        lfo.frequency.value = 4.2;
        lfoGain.gain.value = freq * 0.008; // subtle vibrato depth
        lfo.connect(lfoGain);
        lfoGain.connect(osc1.frequency);
        lfoGain.connect(osc2.frequency);

        osc1.connect(filter);
        osc2.connect(filter);

        filter.frequency.setValueAtTime(250, time);
        filter.frequency.exponentialRampToValueAtTime(150, time + duration); // darken over time

        // Slow swelling string attack (0.8s) and smooth decay
        gainNode.gain.setValueAtTime(0, time);
        gainNode.gain.linearRampToValueAtTime(volume, time + 0.8);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, time + duration);

        lfo.start(time);
        lfo.stop(time + duration);
        osc1.start(time);
        osc1.stop(time + duration);
        osc2.start(time);
        osc2.stop(time + duration);

      } else if (instrument === 'piano') {
        // Felt Piano: warm sine layer + soft triangle transient strike
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();

        osc1.type = 'sine';
        osc2.type = 'triangle';

        osc1.frequency.setValueAtTime(freq, time);
        osc2.frequency.setValueAtTime(freq, time);

        const transientGain = ctx.createGain();
        transientGain.gain.setValueAtTime(volume * 0.35, time);
        transientGain.gain.exponentialRampToValueAtTime(0.0001, time + 0.15); // rapid decay of attack transient
        osc2.connect(transientGain);
        transientGain.connect(filter);

        osc1.connect(filter);

        filter.frequency.setValueAtTime(320, time);

        // felt piano volume envelope
        gainNode.gain.setValueAtTime(0, time);
        gainNode.gain.linearRampToValueAtTime(volume, time + 0.05); // soft strike attack
        gainNode.gain.exponentialRampToValueAtTime(0.0001, time + duration);

        osc1.start(time);
        osc1.stop(time + duration);
        osc2.start(time);
        osc2.stop(time + duration);

      } else if (instrument === 'bass') {
        // Sub-bass / cellistic low-frequency drone layer
        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, time);
        osc.connect(filter);

        filter.frequency.setValueAtTime(100, time); // highly filtered lowpass

        gainNode.gain.setValueAtTime(0, time);
        gainNode.gain.linearRampToValueAtTime(volume, time + 1.2); // slow fade-in swell
        gainNode.gain.exponentialRampToValueAtTime(0.0001, time + duration);

        osc.start(time);
        osc.stop(time + duration);
      }
    } catch (e) {
      if (import.meta.env.DEV) {
        console.warn('Classical note play failed', e);
      }
    }
  };

  const playMeasure = () => {
    if (ctx.state === 'suspended') return;

    const now = ctx.currentTime;
    const piece = pieces[currentPieceIndex];
    const measure = piece.measures[currentMeasureIndex];

    // 1. Play deep cellistic drone (constant low bass, 0.035 volume)
    playNote(measure.bass, now, 'bass', piece.measureDuration / 1000 + 0.5, 0.035);

    // 2. Play right-hand notes and harmonies based on piece
    if (piece.type === 'moonlight') {
      const triplet = measure.triplet;
      for (let i = 0; i < 4; i++) {
        const setOffset = i * (piece.measureDuration / 4000);
        playNote(triplet[0], now + setOffset + 0.0, 'piano', 1.8, 0.015);
        playNote(triplet[1], now + setOffset + 0.25, 'piano', 1.8, 0.015);
        playNote(triplet[2], now + setOffset + 0.5, 'piano', 1.8, 0.015);
      }
    } else if (piece.type === 'chopin_prelude') {
      const chord = measure.chord;
      const melody = measure.melody;

      // Pulse felt piano chords twice per measure
      chord.forEach((freq) => {
        playNote(freq, now + 0.2, 'piano', 2.0, 0.010);
        playNote(freq, now + 2.2, 'piano', 2.0, 0.010);
      });

      // Long sobbing violin melody string note
      playNote(melody, now + 0.5, 'string', 3.8, 0.022);

    } else if (piece.type === 'albinoni') {
      const chord = measure.chord;
      const melody = measure.melody;

      chord.forEach((freq, idx) => {
        playNote(freq, now + 0.8 + idx * 0.15, 'string', 3.2, 0.012);
      });

      playNote(melody, now + 1.2, 'string', 2.8, 0.018);

    } else if (piece.type === 'funeral') {
      const chord = measure.chord;
      const melody = measure.melody;

      // Pulse piano chords on beats 2, 3, 4
      const beatLen = piece.measureDuration / 4000;
      chord.forEach((freq) => {
        playNote(freq, now + beatLen, 'piano', 1.5, 0.010);
        playNote(freq, now + beatLen * 2, 'piano', 1.5, 0.010);
        playNote(freq, now + beatLen * 3, 'piano', 1.5, 0.010);
      });

      // Sobbing high melody note
      playNote(melody, now + 0.4, 'string', 3.2, 0.022);

    } else if (piece.type === 'pathetique') {
      const chord = measure.chord;
      const melody = measure.melody;

      chord.forEach((freq, idx) => {
        playNote(freq, now + 0.6 + idx * 0.2, 'string', 3.5, 0.012);
      });

      playNote(melody, now + 1.0, 'string', 3.2, 0.018);

    } else if (piece.type === 'barber') {
      const chord = measure.chord;
      const melody = measure.melody;

      chord.forEach((freq, idx) => {
        playNote(freq, now + idx * 0.3, 'string', 4.2, 0.010);
      });

      // Soaring, mournful string melody
      playNote(melody, now + 0.8, 'string', 3.8, 0.016);
    }

    // Advance measure index
    currentMeasureIndex = (currentMeasureIndex + 1) % piece.measures.length;

    // After we play all measures of the current piece, transition to a new piece randomly!
    if (currentMeasureIndex === 0) {
      if (pieces.length > 1) {
        let nextPieceIndex = currentPieceIndex;
        while (nextPieceIndex === currentPieceIndex) {
          nextPieceIndex = Math.floor(Math.random() * pieces.length);
        }
        currentPieceIndex = nextPieceIndex;
      }
      if (import.meta.env.DEV) {
        console.log(`[AlterScore Audio] Transitioning to: ${pieces[currentPieceIndex].name}`);
      }

      // Re-schedule interval for the new piece's tempo
      clearInterval(ambientInterval);
      ambientInterval = setInterval(playMeasure, pieces[currentPieceIndex].measureDuration);
    }
  };

  // Start loop for the initial piece
  if (import.meta.env.DEV) {
    console.log(`[AlterScore Audio] Starting playback with: ${pieces[currentPieceIndex].name}`);
  }
  playMeasure();
  ambientInterval = setInterval(playMeasure, pieces[currentPieceIndex].measureDuration);
};

export default function useSound() {
  const audioCtxRef = useRef(null);
  const [muted, setMuted] = useState(soundMuted);

  useEffect(() => {
    const handleMutedChange = (event) => {
      setMuted(Boolean(event.detail));
    };

    window.addEventListener('alterscore_sound_muted_change', handleMutedChange);
    return () => window.removeEventListener('alterscore_sound_muted_change', handleMutedChange);
  }, []);

  const getAudioContext = () => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return null;
    if (soundMuted) {
      stopAmbient();
      return null;
    }

    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }

    const ctx = audioCtxRef.current;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    // Lazy start ambient pad on first interaction
    if (!ambientInterval) {
      startAmbient(ctx);
    }

    return ctx;
  };

  const initAudio = () => {
    getAudioContext();
  };

  const toggleMuted = () => {
    soundMuted = !soundMuted;
    localStorage.setItem('alterscore_sound_muted', String(soundMuted));
    if (soundMuted) {
      stopAmbient();
      audioCtxRef.current?.suspend?.();
    }
    setMuted(soundMuted);
    notifySoundPreference();
  };

  const playClick = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    // Transient tick/chirp for precision
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.type = 'triangle';
    osc1.frequency.setValueAtTime(1500, now);
    osc1.frequency.exponentialRampToValueAtTime(300, now + 0.04);
    gain1.gain.setValueAtTime(0.025, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

    // Warm body resonance for depth
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(250, now);
    osc2.frequency.exponentialRampToValueAtTime(120, now + 0.12);
    gain2.gain.setValueAtTime(0.035, now);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

    osc1.start(now);
    osc1.stop(now + 0.04);
    
    osc2.start(now);
    osc2.stop(now + 0.12);
  };

  const playSelect = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(660, now);

    gain.gain.setValueAtTime(0.03, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);

    osc.start(now);
    osc.stop(now + 0.06);
  };

  const playHover = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, now);

    gain.gain.setValueAtTime(0.015, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.03);

    osc.start(now);
    osc.stop(now + 0.03);
  };

  const playTransition = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const bufferSize = ctx.sampleRate * 0.2; // 200ms
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);

    // Generate white noise
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noiseNode = ctx.createBufferSource();
    noiseNode.buffer = buffer;

    // Filter noise to create a sweep
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(100, now);
    filter.frequency.exponentialRampToValueAtTime(1500, now + 0.2);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.05, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

    noiseNode.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    noiseNode.start(now);
    noiseNode.stop(now + 0.2);
  };

  const playSuccess = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    // Two-tone chord: C5 (523.25 Hz) and E5 (659.25 Hz)
    const frequencies = [523.25, 659.25];
    
    frequencies.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.type = 'triangle';
      
      // Delay second oscillator slightly for arpeggio effect
      const startOffset = idx * 0.05;
      osc.frequency.setValueAtTime(freq, now + startOffset);

      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.03, now + startOffset + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + startOffset + 0.25);

      osc.start(now + startOffset);
      osc.stop(now + startOffset + 0.25);
    });
  };

  const playStep = () => {
    const ctx = getAudioContext();
    if (!ctx) return;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(550, now);

    gain.gain.setValueAtTime(0.025, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

    osc.start(now);
    osc.stop(now + 0.08);
  };

  return {
    initAudio,
    muted,
    toggleMuted,
    playClick,
    playSelect,
    playHover,
    playTransition,
    playSuccess,
    playStep,
  };
}
