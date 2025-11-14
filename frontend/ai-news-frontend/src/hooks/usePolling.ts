import { useState, useEffect, useCallback } from 'react';

interface UsePollingOptions<T> {
  fetchFunction: () => Promise<T>;
  interval?: number;
  enabled?: boolean;
  onError?: (error: Error) => void;
}

export function usePolling<T>({
  fetchFunction,
  interval = 30000,
  enabled = true,
  onError
}: UsePollingOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const result = await fetchFunction();
      setData(result);
      setLastUpdate(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      onError?.(err as Error);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, enabled, onError]);

  useEffect(() => {
    fetchData(); // Initial fetch

    if (!enabled) return;

    const intervalId = setInterval(fetchData, interval);

    return () => clearInterval(intervalId);
  }, [fetchData, interval, enabled]);

  const refetch = useCallback(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    lastUpdate,
    refetch
  };
}