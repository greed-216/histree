import { useEffect, useLayoutEffect, useRef } from "react";
import { useLocation, useNavigationType } from "react-router-dom";
const positions = new Map<string, number>();

/** Cached feeds are available on the first render, so browser Back can restore their position. */
export function useScrollRestoration() {
  const previousPath = useRef<{ pathname: string; key: string } | null>(null);
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
    const retainPosition = previousPath.current?.pathname === '/timeline' && previousPath.current.key !== location.key && location.pathname === '/timeline';
    previousPath.current = { pathname: location.pathname, key: location.key };
    if (retainPosition) positions.set(location.key, window.scrollY);
    const remember = () => {
      positions.set(location.key, window.scrollY);
      if (positions.size > 40) positions.delete(positions.keys().next().value!);
    };
    window.addEventListener("scroll", remember, { passive: true });
    const frame = location.hash || retainPosition
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
