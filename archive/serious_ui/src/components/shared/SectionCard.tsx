import type { ReactNode } from "react";

import { PanelHeader } from "./PanelHeader";

type SectionCardProps = {
  eyebrow: string;
  title: string;
  titleId?: string;
  lede?: string;
  meta?: ReactNode;
  className?: string;
  children: ReactNode;
};

export function SectionCard({
  eyebrow,
  title,
  titleId,
  lede,
  meta,
  className,
  children,
}: SectionCardProps): JSX.Element {
  return (
    <section className={`subsection${className ? ` ${className}` : ""}`} aria-labelledby={titleId}>
      <PanelHeader eyebrow={eyebrow} title={title} titleId={titleId} lede={lede} meta={meta} />
      {children}
    </section>
  );
}
