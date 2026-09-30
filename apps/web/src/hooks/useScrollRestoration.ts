import { useEffect, useLayoutEffect } from "react";
import { useLocation, useNavigationType } from "react-router-dom";
const positions = new Map<string, number>();

/** Cached feeds are available on the first render, so browser Back can restore their position. */
export function useScrollRestoration() {
  const location = useLocation(),
    navigation = useNavigationType();
  useEffect(() => {
    const original = history.scrollRestoration;
    history.scrollRestoration = "manual";
    return () => {
      history.scrollRestoration = original;
    };
  }, []);
  useLayoutEffect(() => {
    const remember = () => {
      positions.set(location.key, window.scrollY);
      if (positions.size > 40) positions.delete(positions.keys().next().value!);
    };
    window.addEventListener("scroll", remember, { passive: true });
    const frame = location.hash
      ? undefined
      : requestAnimationFrame(() => {
          window.scrollTo(
            0,
            navigation === "POP" ? (positions.get(location.key) ?? 0) : 0,
          );
        });
    return () => {
      window.removeEventListener("scroll", remember);
      if (frame !== undefined) cancelAnimationFrame(frame);
    };
  }, [
    location.key,
    location.pathname,
    location.search,
    location.hash,
    navigation,
  ]);
}
