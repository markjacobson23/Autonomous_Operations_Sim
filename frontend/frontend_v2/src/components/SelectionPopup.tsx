import type { SelectionPresentation } from "../adapters/selectionModel";

type SelectionPopupProps = {
  presentation: SelectionPresentation | null;
};

export function SelectionPopup({ presentation }: SelectionPopupProps): JSX.Element | null {
  if (presentation === null) {
    return null;
  }

  return (
    <aside className="selection-popup" aria-live="polite">
      <div className="selection-popup-head">
        <div>
          <p className="panel-kicker">Selection</p>
          <h3>{presentation.title}</h3>
        </div>
        <span className="selection-popup-badge">{presentation.badge}</span>
      </div>
      <p className="selection-popup-summary">{presentation.summary}</p>
      <p className="selection-popup-context">{presentation.context}</p>
      <div className="selection-popup-details">
        {presentation.details.slice(0, 3).map((detail) => (
          <div key={detail.label} className="selection-popup-detail">
            <span>{detail.label}</span>
            <strong>{detail.value}</strong>
          </div>
        ))}
      </div>
      {presentation.notes.length > 0 ? (
        <p className="selection-popup-note">{presentation.notes[0]}</p>
      ) : null}
    </aside>
  );
}
