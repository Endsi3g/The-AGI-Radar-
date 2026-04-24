"use client";

import { useState, useEffect, useCallback } from "react";
import { ChevronRight, ChevronLeft, Maximize2, Minimize2, X } from "lucide-react";

interface Section {
  title: string;
  content: string;
}

interface Props {
  sections: Section[];
  leadName: string;
  onClose: () => void;
}

export function Teleprompter({ sections, leadName, onClose }: Props) {
  const [current, setCurrent] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);

  const next = useCallback(() => setCurrent((c) => Math.min(c + 1, sections.length - 1)), [sections.length]);
  const prev = useCallback(() => setCurrent((c) => Math.max(c - 1, 0)), []);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {
        e.preventDefault();
        next();
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        prev();
      }
      if (e.key === "Escape") {
        if (fullscreen) setFullscreen(false);
        else onClose();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [next, prev, fullscreen, onClose]);

  const section = sections[current];
  const isFirst = current === 0;
  const isLast = current === sections.length - 1;

  const containerClass = fullscreen
    ? "fixed inset-0 z-50 bg-gray-950 flex flex-col"
    : "bg-gray-950 rounded-2xl flex flex-col min-h-[400px]";

  return (
    <div className={containerClass}>
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm">Téléprompter</span>
          <span className="text-white font-semibold">{leadName}</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Step indicators */}
          <div className="flex gap-1">
            {sections.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrent(i)}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === current ? "bg-blue-400" : i < current ? "bg-emerald-500" : "bg-gray-700"
                }`}
              />
            ))}
          </div>
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-1.5 text-gray-400 hover:text-white"
          >
            {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-white">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 py-10">
        <div className="w-full max-w-3xl">
          <p className="text-blue-400 text-sm font-medium uppercase tracking-widest mb-4">
            {current + 1} / {sections.length} — {section.title}
          </p>
          <p className={`text-white leading-relaxed whitespace-pre-wrap ${
            fullscreen ? "text-3xl" : "text-xl"
          }`}>
            {section.content}
          </p>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800">
        <button
          onClick={prev}
          disabled={isFirst}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={16} /> Précédent
        </button>
        <span className="text-gray-600 text-xs">← → ou Espace pour avancer</span>
        <button
          onClick={next}
          disabled={isLast}
          className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
            isLast
              ? "text-gray-600 cursor-not-allowed"
              : "text-white bg-blue-600 hover:bg-blue-700"
          }`}
        >
          Suivant <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

export function parseScriptToSections(scriptBody: string): Section[] {
  const lines = scriptBody.split("\n");
  const sections: Section[] = [];
  let currentTitle = "";
  let currentLines: string[] = [];

  for (const line of lines) {
    const headerMatch = line.match(/^===\s*(.+?)\s*===$/);
    if (headerMatch) {
      if (currentTitle && currentLines.some((l) => l.trim())) {
        sections.push({ title: currentTitle, content: currentLines.join("\n").trim() });
      }
      currentTitle = headerMatch[1];
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }
  if (currentTitle && currentLines.some((l) => l.trim())) {
    sections.push({ title: currentTitle, content: currentLines.join("\n").trim() });
  }

  return sections.length > 0
    ? sections
    : [{ title: "Script", content: scriptBody }];
}
