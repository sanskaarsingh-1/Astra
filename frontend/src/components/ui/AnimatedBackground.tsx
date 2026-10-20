"use client";

import React, { useEffect, useRef } from "react";
import { animate, random } from "animejs";

export function AnimatedBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    
    // Clear any existing children to prevent duplicates on re-render in dev
    container.innerHTML = "";

    const numNodes = 18;
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < numNodes; i++) {
      const el = document.createElement("div");
      el.classList.add("bg-node");
      
      const size = Math.random() * 2 + 1;
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.background = "rgba(255, 255, 255, 0.35)";
      el.style.borderRadius = "50%";
      el.style.position = "absolute";
      el.style.left = `${Math.random() * 100}vw`;
      el.style.top = `${Math.random() * 100}vh`;
      el.style.willChange = "transform, opacity";
      el.style.transform = "translateZ(0)";
      
      fragment.appendChild(el);
    }

    container.appendChild(fragment);

    // Hardware-accelerated subtle floating animation
    animate(".bg-node", {
      translateX: () => `${random(-12, 12)}vw`,
      translateY: () => `${random(-12, 12)}vh`,
      opacity: [0.1, 0.35, 0.1],
      ease: "linear",
      duration: () => random(18000, 30000),
      delay: () => random(0, 1500),
      alternate: true,
      loop: true,
    });
  }, []);

  return (
    <div className="fixed inset-0 -z-40 overflow-hidden pointer-events-none bg-transparent [transform:translateZ(0)]">
      {/* Subtle starlight particles container */}
      <div ref={containerRef} className="absolute inset-0" />
      
      {/* Ultra-efficient zero-blur radial ambient glow (prevents GPU fill-rate lag) */}
      <div className="absolute top-0 left-0 w-[50vw] h-[50vw] bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.025),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[50vw] h-[50vw] bg-[radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.02),transparent_70%)] pointer-events-none" />
    </div>
  );
}
