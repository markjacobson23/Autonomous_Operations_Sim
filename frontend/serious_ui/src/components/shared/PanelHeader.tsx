import type { ReactNode } from "react";

type PanelHeaderProps = {
  eyebrow: string;
  title: string;
  titleId?: string;
  lede?: string;
  meta?: ReactNode;
  className?: string;
};

export function PanelHeader({
  eyebrow,
  title,
  titleId,
  lede,
  meta,
  className,
}: PanelHeaderProps): JSX.Element {
  return (
    <div className={`panel-header${className ? ` ${className}` : ""}`}>
      <div className="panel-copy">
        <p className="eyebrow">{eyebrow}</p>
        <h2 id={titleId}>{title}</h2>
        {lede ? <p className="panel-lede">{lede}</p> : null}
      </div>
      {meta ? <div className="panel-meta">{meta}</div> : null}
    </div>
  );
}
