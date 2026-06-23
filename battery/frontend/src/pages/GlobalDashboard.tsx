import React, { useState } from "react";
import Dashboard from "./Dashboard";
import { useSetups } from "../context/SetupContext";

const GlobalDashboard: React.FC = () => {
  const { activeSetup, loading: setupLoading } = useSetups();
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const inputStyle: React.CSSProperties = {
    padding: "0.6rem",
    borderRadius: "8px",
    border: "1px solid #cbd5e0",
    background: "#fff",
    fontSize: "0.9rem",
    color: "#2d3748",
    outline: "none",
    width: "150px",
  };

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "2rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
          padding: "0.5rem 0",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.75rem", color: "#1a202c" }}>
            Global Analysis
          </h1>
          <p
            style={{
              color: "#718096",
              margin: "0.25rem 0 0 0",
              fontSize: "1rem",
            }}
          >
            Aggregated performance for{" "}
            <strong>{activeSetup?.name || "..."}</strong>
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            background: "#fff",
            padding: "1rem",
            borderRadius: "12px",
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        >
          <div
            style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
          >
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: "bold",
                  color: "#a0aec0",
                  textTransform: "uppercase",
                  marginBottom: "0.25rem",
                }}
              >
                From
              </span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: "bold",
                  color: "#a0aec0",
                  textTransform: "uppercase",
                  marginBottom: "0.25rem",
                }}
              >
                To
              </span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <button
            onClick={() => {
              setStartDate("");
              setEndDate("");
            }}
            style={{
              padding: "0.6rem 1rem",
              background: "#f7fafc",
              color: "#4a5568",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "0.9rem",
              alignSelf: "flex-end",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = "#edf2f7")}
            onMouseOut={(e) => (e.currentTarget.style.background = "#f7fafc")}
          >
            Reset
          </button>
        </div>
      </header>

      {/* Render the Dashboard component as a child */}
      <div style={{ minHeight: "600px" }}>
        {setupLoading ? (
          <p>Loading setups...</p>
        ) : !activeSetup ? (
          <div
            style={{
              textAlign: "center",
              padding: "5rem",
              background: "#fff",
              borderRadius: "16px",
              border: "1px solid #e2e8f0",
            }}
          >
            <h2 style={{ color: "#4a5568" }}>No Setup Selected</h2>
            <p style={{ color: "#718096" }}>
              Please select a setup in the navbar to view the analysis.
            </p>
          </div>
        ) : (
          <Dashboard startDate={startDate} endDate={endDate} isGlobal={true} />
        )}
      </div>
    </div>
  );
};

export default GlobalDashboard;
