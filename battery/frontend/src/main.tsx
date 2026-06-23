import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { SetupProvider } from "./context/SetupContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SetupProvider>
      <App />
    </SetupProvider>
  </React.StrictMode>,
);
