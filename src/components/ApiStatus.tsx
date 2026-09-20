import { useEffect, useState } from "react";
import { getHealth } from "../api/todos";
import type { Health } from "../types";

export default function ApiStatus() {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((result) => {
        if (!cancelled) setHealth(result);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return <p className="status down">API unreachable</p>;
  }
  if (!health) {
    return <p className="status">Checking the API…</p>;
  }
  return (
    <p className="status up">
      API online · release {health.version.slice(0, 7)}
    </p>
  );
}
