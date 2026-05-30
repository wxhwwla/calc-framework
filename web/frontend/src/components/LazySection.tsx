import { useEffect, useRef, useState, type ReactNode } from "react";
import { Skeleton } from "@mui/material";

interface LazySectionProps {
  children: ReactNode;
  height?: number;
  placeholder?: ReactNode;
}

export default function LazySection({ children, height = 120, placeholder }: LazySectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.unobserve(el);
        }
      },
      { rootMargin: "100px" },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref}>
      {visible ? (
        children
      ) : (
        placeholder || (
          <Skeleton
            variant="rectangular"
            height={height}
            sx={{ borderRadius: 1, mb: 2 }}
            animation="wave"
          />
        )
      )}
    </div>
  );
}
