import { useEffect, useState } from "react";

export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const reload = () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => setState({ data: null, loading: false, error }));
  };

  useEffect(reload, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, reload };
}
