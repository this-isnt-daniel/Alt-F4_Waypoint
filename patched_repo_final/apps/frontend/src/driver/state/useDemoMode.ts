import { useEffect, useState } from "react";

export function useDemoMode(): boolean {
  const [demo, setDemo] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const searchParams = new URLSearchParams(window.location.search);
    const hashQuery = window.location.hash.includes("?")
      ? window.location.hash.split("?")[1]
      : "";
    const hashParams = new URLSearchParams(hashQuery);
    return searchParams.get("demo") === "1" || hashParams.get("demo") === "1";
  });

  useEffect(() => {
    function handleUpdate() {
      const searchParams = new URLSearchParams(window.location.search);
      const hashQuery = window.location.hash.includes("?")
        ? window.location.hash.split("?")[1]
        : "";
      const hashParams = new URLSearchParams(hashQuery);
      setDemo(
        searchParams.get("demo") === "1" || hashParams.get("demo") === "1",
      );
    }

    window.addEventListener("hashchange", handleUpdate);
    window.addEventListener("popstate", handleUpdate);
    return () => {
      window.removeEventListener("hashchange", handleUpdate);
      window.removeEventListener("popstate", handleUpdate);
    };
  }, []);

  return demo;
}
