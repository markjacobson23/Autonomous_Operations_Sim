type StateCalloutProps = {
  title: string;
  copy: string;
  action?: string;
  tone?: "muted" | "loading" | "warning" | "error" | "success";
  className?: string;
};

export function StateCallout({
  title,
  copy,
  action,
  tone = "muted",
  className,
}: StateCalloutProps): JSX.Element {
  return (
    <div className={`state-callout state-callout-${tone}${className ? ` ${className}` : ""}`}>
      <strong className="state-callout-title">{title}</strong>
      <p className="state-callout-copy">{copy}</p>
      {action ? <p className="state-callout-action">{action}</p> : null}
    </div>
  );
}
