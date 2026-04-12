import { buildLiveBundleViewModel } from "./adapters/liveBundle";
import { FrontendShell } from "./components/FrontendShell";
import { useLiveSessionBundle } from "./hooks/useLiveSessionBundle";
import { useFrontendUiState } from "./state/frontendUiState";

function App(): JSX.Element {
  const bundleResource = useLiveSessionBundle();
  const bundleViewModel = buildLiveBundleViewModel(bundleResource);
  const uiState = useFrontendUiState();

  return <FrontendShell bundle={bundleViewModel} uiState={uiState.state} actions={uiState.actions} />;
}

export default App;
