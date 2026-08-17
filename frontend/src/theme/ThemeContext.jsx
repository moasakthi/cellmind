import { createContext, useContext, useEffect, useState } from "react";

export const PALETTES = [
  { id: "nova", label: "Nova (default)" },
  { id: "teal", label: "EL Teal" },
  { id: "amber", label: "Furnace Amber" },
  { id: "indigo", label: "Night Line Indigo" },
  { id: "mono", label: "Mono Readout" },
];

const ThemeContext = createContext(null);
const KEY_MODE = "cellmind.mode";
const KEY_PALETTE = "cellmind.palette";

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState(() => localStorage.getItem(KEY_MODE) || "dark");
  const [palette, setPalette] = useState(() => localStorage.getItem(KEY_PALETTE) || "nova");

  useEffect(() => {
    const root = document.documentElement;
    if (mode === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
    localStorage.setItem(KEY_MODE, mode);
  }, [mode]);

  useEffect(() => {
    document.documentElement.setAttribute("data-palette", palette);
    localStorage.setItem(KEY_PALETTE, palette);
  }, [palette]);

  function toggleMode() {
    setMode((m) => (m === "dark" ? "light" : m === "light" ? "system" : "dark"));
  }

  return (
    <ThemeContext.Provider value={{ mode, setMode, toggleMode, palette, setPalette }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
