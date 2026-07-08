import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "../api";

// Subscribes to a room ("feed" or a quiz id); returns latest event per type.
export default function useQuizSocket(room) {
  const [events, setEvents] = useState({});
  const wsRef = useRef(null);

  useEffect(() => {
    if (!room) return;
    const path = room === "feed" ? "/ws/feed" : `/ws/quiz/${room}`;
    const ws = new WebSocket(`${WS_BASE}${path}`);
    wsRef.current = ws;

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type) setEvents((prev) => ({ ...prev, [data.type]: data }));
      } catch {
        /* ignore malformed frames */
      }
    };

    return () => ws.close();
  }, [room]);

  return events;
}
