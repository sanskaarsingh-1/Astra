'use client';

import * as React from 'react';
import Link from 'next/link';
import { ArrowRight, ArrowUpRight, ExternalLink, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  text?: React.ReactNode;
  children?: React.ReactNode;
  href?: string;
  variant?: 'primary' | 'outline' | 'ghost';
  icon?: LucideIcon;
  external?: boolean;
  className?: string;
}

export function FlowButton({
  text,
  children,
  href,
  variant = 'outline',
  icon: Icon = ArrowRight,
  external = false,
  className,
  disabled,
  onClick,
  type = 'button',
  ...props
}: FlowButtonProps) {
  const content = text || children;
  const isPrimary = variant === 'primary';
  const isDiagonal = Icon === ExternalLink || Icon === ArrowUpRight;

  const innerContent = (
    <>
      {/* Circle expands from center on hover (GPU accelerated scale transform) */}
      <span
        className={cn(
          "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-4 rounded-full opacity-0 pointer-events-none group-hover:scale-[35] group-hover:opacity-100 transition-all duration-500 ease-out",
          isPrimary ? "bg-zinc-950" : "bg-white"
        )}
      />

      {/* Button content (text + animated flowing icon) perfectly aligned in flex flow */}
      <span className="relative z-10 flex items-center justify-center gap-1.5 whitespace-nowrap transition-colors duration-300">
        <span className="inline-block transition-transform duration-300 ease-out group-hover:-translate-x-0.5">
          {content}
        </span>

        {Icon && (
          <span className="relative inline-flex items-center justify-center size-3.5 overflow-hidden shrink-0">
            {/* Primary icon (flows out on hover) */}
            <Icon
              className={cn(
                "size-3.5 shrink-0 transition-all duration-300 ease-out",
                isDiagonal
                  ? "group-hover:translate-x-3.5 group-hover:-translate-y-3.5 group-hover:opacity-0"
                  : "group-hover:translate-x-3.5 group-hover:opacity-0"
              )}
            />

            {/* Secondary icon (flows in on hover) */}
            <Icon
              className={cn(
                "absolute size-3.5 shrink-0 transition-all duration-300 ease-out opacity-0",
                isDiagonal
                  ? "-translate-x-3.5 translate-y-3.5 group-hover:translate-x-0 group-hover:translate-y-0 group-hover:opacity-100"
                  : "-translate-x-3.5 group-hover:translate-x-0 group-hover:opacity-100"
              )}
            />
          </span>
        )}
      </span>
    </>
  );

  const baseClasses = cn(
    "group relative inline-flex items-center justify-center overflow-hidden cursor-pointer transition-all duration-300 ease-out active:scale-95 select-none",
    isPrimary
      ? "bg-white text-zinc-950 border border-white hover:border-transparent hover:text-white"
      : "bg-white/5 text-white border border-white/15 hover:border-transparent hover:text-zinc-950",
    disabled && "opacity-50 cursor-not-allowed pointer-events-none",
    className
  );

  if (href) {
    if (external) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={baseClasses}
        >
          {innerContent}
        </a>
      );
    }

    return (
      <Link href={href} className={baseClasses}>
        {innerContent}
      </Link>
    );
  }

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={baseClasses}
      {...props}
    >
      {innerContent}
    </button>
  );
}

export default FlowButton;
