"use client";

import { Fragment } from "react";

export type SplitLine = string | { text: string; className?: string };

const textOf = (line: SplitLine) => (typeof line === "string" ? line : line.text);
const classOf = (line: SplitLine) => (typeof line === "string" ? "" : (line.className ?? ""));

/**
 * Opt-in per-character heading reveal, for plain-text narrative headings.
 *
 * The visible glyphs are decoration: every line is `aria-hidden` and holds no
 * accessible name. A single visually-hidden copy of the same string supplies the
 * real name, so assistive tech — and `getByRole("heading", { name })` — reads
 * the heading as one ordinary sentence.
 *
 * Two consequences worth knowing before you reach for this:
 *
 * - `innerText` on a split heading contains the text twice (the hidden copy is
 *   not aria-hidden). Never split a heading a test matches by `innerText`.
 * - Words are separate inline-blocks so wrapping still happens between words.
 *   A single unbreakable word longer than the line will overflow, so this suits
 *   display headings, not body copy.
 *
 * Wrapped in prose it would also break selection and find-in-page, so it is
 * deliberately not the default: `SectionHeading` takes a clip wipe instead.
 */
export function SplitHeading({
  lines,
  as: Tag = "h2",
  className = "",
  id,
}: {
  lines: SplitLine[];
  as?: "h1" | "h2" | "h3";
  className?: string;
  id?: string;
}) {
  return (
    <Tag id={id} className={className} data-split>
      <span className="sr-only">{lines.map(textOf).join(" ")}</span>
      {lines.map((line, index) => {
        const words = textOf(line).split(" ");
        return (
          <span key={index} aria-hidden="true" className={`split-line ${classOf(line)}`}>
            {words.map((word, wordIndex) => (
              <Fragment key={wordIndex}>
                <span className="split-word">
                  {Array.from(word).map((char, charIndex) => (
                    <span className="char-mask" key={charIndex}>
                      <span className="char">{char}</span>
                    </span>
                  ))}
                </span>
                {wordIndex < words.length - 1 ? " " : null}
              </Fragment>
            ))}
          </span>
        );
      })}
    </Tag>
  );
}
