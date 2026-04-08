import { useState, useCallback } from "react";

export function useAsync(asyncFn) {
  const [state, setState] = useState({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args) => {
      setState({ data: null, loading: true, error: null });
      try {
        const data = await asyncFn(...args);
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        setState({ data: null, loading: false, error: err.message });
        throw err;
      }
    },
    [asyncFn]
  );

  return { ...state, execute };
}

export function usePolling(asyncFn, interval = 5000) {
  const [isPolling, setIsPolling] = useState(false);
  const [timerId, setTimerId] = useState(null);
  const async_ = useAsync(asyncFn);

  const start = useCallback(() => {
    setIsPolling(true);
    async_.execute();
    const id = setInterval(() => async_.execute(), interval);
    setTimerId(id);
  }, [asyncFn, interval]);

  const stop = useCallback(() => {
    setIsPolling(false);
    if (timerId) clearInterval(timerId);
  }, [timerId]);

  return { ...async_, isPolling, start, stop };
}
