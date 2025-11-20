"use client";

import { useEffect } from "react";

export default function HydrationFix() {
  useEffect(() => {
    // Suppress hydration warning in development
    if (typeof window !== "undefined") {
      // Remove DarkReader attributes that cause hydration issues
      const removeDarkReaderAttrs = () => {
        const elements = document.querySelectorAll("[data-darkreader-inline-]");
        elements.forEach((el) => {
          const attributes = Array.from(el.attributes);
          attributes.forEach((attr) => {
            if (attr.name.startsWith("data-darkreader-inline-")) {
              el.removeAttribute(attr.name);
            }
          });
        });
      };

      // Run immediately and on DOM changes
      removeDarkReaderAttrs();

      const observer = new MutationObserver(() => {
        removeDarkReaderAttrs();
      });

      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-darkreader-mode", "data-darkreader-scheme"],
        subtree: true,
      });

      // Also remove any style attributes with DarkReader custom properties
      const removeDarkReaderStyles = () => {
        const elements = document.querySelectorAll("[style*='--darkreader']");
        elements.forEach((el) => {
          const style = el.getAttribute("style");
          if (style) {
            const cleanedStyle = style
              .split(";")
              .filter((prop) => !prop.trim().startsWith("--darkreader"))
              .join("; ");
            if (cleanedStyle.trim()) {
              el.setAttribute("style", cleanedStyle);
            } else {
              el.removeAttribute("style");
            }
          }
        });
      };

      // Run periodically to catch dynamically added elements
      const interval = setInterval(removeDarkReaderStyles, 1000);

      return () => {
        observer.disconnect();
        clearInterval(interval);
      };
    }
  }, []);

  return null;
}
