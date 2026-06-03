import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollToPlugin } from "gsap/ScrollToPlugin";

gsap.registerPlugin(ScrollToPlugin);

const ANCHORS = [0, 2000, 2500, 4200, 4600, 7000, 7500, 9200, 9600, 12000, 12700];
const FREE_ZONES = [
  [2500, 4200],
  [7500, 9200]
];
const TOTAL_FRAMES = 12700;

export default function useSnapScroll(enabled) {
  const isAnimatingRef = useRef(false);
  const cooldownRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    const getMaxScroll = () => document.documentElement.scrollHeight - window.innerHeight;

    const getFrameFromScroll = (scroll) => {
      const maxScroll = getMaxScroll();
      if (maxScroll <= 0) return 0;
      return (scroll / maxScroll) * TOTAL_FRAMES;
    };

    const getScrollFromFrame = (frame) => {
      const maxScroll = getMaxScroll();
      return (frame / TOTAL_FRAMES) * maxScroll;
    };

    const isInsideFreeZone = (frame) => {
      return FREE_ZONES.some(([start, end]) => frame > start && frame < end);
    };

    const getNearestAnchorIndex = (frame) => {
      return ANCHORS.reduce((nearestIdx, anchorFrame, idx) => {
        return Math.abs(frame - anchorFrame) < Math.abs(frame - ANCHORS[nearestIdx]) ? idx : nearestIdx;
      }, 0);
    };

    const animateToFrame = (targetFrame) => {
      isAnimatingRef.current = true;
      const targetScroll = getScrollFromFrame(targetFrame);

      gsap.to(window, {
        scrollTo: { y: targetScroll, autoKill: false },
        duration: 1.1,
        ease: "power3.inOut",
        overwrite: "auto",
        onComplete: () => {
          cooldownRef.current = true;
          setTimeout(() => {
            cooldownRef.current = false;
            isAnimatingRef.current = false;
          }, 300);
        }
      });
    };

    const handleWheel = (e) => {
      if (isAnimatingRef.current || cooldownRef.current) {
        e.preventDefault();
        return;
      }

      const currentScroll = window.scrollY;
      const currentFrame = getFrameFromScroll(currentScroll);

      if (isInsideFreeZone(currentFrame)) {
        const delta = e.deltaY;
        const nextEstimatedFrame = getFrameFromScroll(currentScroll + delta);
        
        // Exiting free zone 1 down
        if (currentFrame <= 4200 && nextEstimatedFrame >= 4200 && delta > 0) {
          e.preventDefault();
          animateToFrame(4600);
        }
        // Exiting free zone 1 up
        else if (currentFrame >= 2500 && nextEstimatedFrame <= 2500 && delta < 0) {
          e.preventDefault();
          animateToFrame(2000);
        }
        // Exiting free zone 2 down
        else if (currentFrame <= 9200 && nextEstimatedFrame >= 9200 && delta > 0) {
          e.preventDefault();
          animateToFrame(9600);
        }
        // Exiting free zone 2 up
        else if (currentFrame >= 7500 && nextEstimatedFrame <= 7500 && delta < 0) {
          e.preventDefault();
          animateToFrame(7000);
        }
        return;
      }

      e.preventDefault();

      const direction = e.deltaY > 0 ? 1 : -1;
      const nearestIdx = getNearestAnchorIndex(currentFrame);
      
      let targetIdx = nearestIdx;
      if (direction > 0) {
        targetIdx = Math.min(nearestIdx + 1, ANCHORS.length - 1);
        if (currentFrame >= ANCHORS[nearestIdx] && targetIdx === nearestIdx) {
          targetIdx = Math.min(nearestIdx + 1, ANCHORS.length - 1);
        }
      } else {
        targetIdx = Math.max(nearestIdx - 1, 0);
        if (currentFrame <= ANCHORS[nearestIdx] && targetIdx === nearestIdx) {
          targetIdx = Math.max(nearestIdx - 1, 0);
        }
      }

      animateToFrame(ANCHORS[targetIdx]);
    };

    let touchStartY = 0;
    const handleTouchStart = (e) => {
      touchStartY = e.touches[0].clientY;
    };

    const handleTouchMove = (e) => {
      if (isAnimatingRef.current || cooldownRef.current) {
        e.preventDefault();
        return;
      }

      const currentScroll = window.scrollY;
      const currentFrame = getFrameFromScroll(currentScroll);

      if (isInsideFreeZone(currentFrame)) {
        return;
      }

      e.preventDefault();
    };

    const handleTouchEnd = (e) => {
      if (isAnimatingRef.current || cooldownRef.current) return;

      const touchEndY = e.changedTouches[0].clientY;
      const deltaY = touchStartY - touchEndY;

      if (Math.abs(deltaY) < 35) return;

      const currentScroll = window.scrollY;
      const currentFrame = getFrameFromScroll(currentScroll);

      if (isInsideFreeZone(currentFrame)) {
        const nextEstimatedFrame = getFrameFromScroll(currentScroll + deltaY);
        if (currentFrame <= 4200 && nextEstimatedFrame >= 4200 && deltaY > 0) {
          animateToFrame(4600);
        } else if (currentFrame >= 2500 && nextEstimatedFrame <= 2500 && deltaY < 0) {
          animateToFrame(2000);
        } else if (currentFrame <= 9200 && nextEstimatedFrame >= 9200 && deltaY > 0) {
          animateToFrame(9600);
        } else if (currentFrame >= 7500 && nextEstimatedFrame <= 7500 && deltaY < 0) {
          animateToFrame(7000);
        }
        return;
      }

      const direction = deltaY > 0 ? 1 : -1;
      const nearestIdx = getNearestAnchorIndex(currentFrame);
      let targetIdx = nearestIdx;

      if (direction > 0) {
        targetIdx = Math.min(nearestIdx + 1, ANCHORS.length - 1);
      } else {
        targetIdx = Math.max(nearestIdx - 1, 0);
      }

      animateToFrame(ANCHORS[targetIdx]);
    };

    const handleKeyDown = (e) => {
      const keys = ["ArrowDown", "ArrowUp", "PageDown", "PageUp", " ", "Spacebar"];
      if (!keys.includes(e.key)) return;

      e.preventDefault();

      if (isAnimatingRef.current || cooldownRef.current) return;

      const currentScroll = window.scrollY;
      const currentFrame = getFrameFromScroll(currentScroll);
      const nearestIdx = getNearestAnchorIndex(currentFrame);
      let targetIdx = nearestIdx;

      if (e.key === "ArrowDown" || e.key === "PageDown" || e.key === " " || e.key === "Spacebar") {
        targetIdx = Math.min(nearestIdx + 1, ANCHORS.length - 1);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        targetIdx = Math.max(nearestIdx - 1, 0);
      }

      animateToFrame(ANCHORS[targetIdx]);
    };

    window.addEventListener("wheel", handleWheel, { passive: false });
    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    window.addEventListener("touchmove", handleTouchMove, { passive: false });
    window.addEventListener("touchend", handleTouchEnd, { passive: true });
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("wheel", handleWheel);
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleTouchEnd);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled]);

  return {
    scrollToWaypoint: (index) => {
      const pauseFrames = [0, 2000, 4600, 7000, 9600, 12000];
      const targetFrame = pauseFrames[Math.min(index, pauseFrames.length - 1)];
      
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const targetScroll = (targetFrame / TOTAL_FRAMES) * maxScroll;

      isAnimatingRef.current = true;
      gsap.to(window, {
        scrollTo: { y: targetScroll, autoKill: false },
        duration: 1.1,
        ease: "power3.inOut",
        overwrite: "auto",
        onComplete: () => {
          cooldownRef.current = true;
          setTimeout(() => {
            cooldownRef.current = false;
            isAnimatingRef.current = false;
          }, 300);
        }
      });
    }
  };
}
