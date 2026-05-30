import React, { useState } from 'react';
import MainPage from "./pages/MainPage";
import { appState as initialAppState } from "./state/appState";

const App = () => {
  const [appState, setAppState] = useState(initialAppState);

  return (
    <MainPage
      appState={appState}
      setAppState={setAppState}
      userId="u001"
    />
  );
};

export default App;