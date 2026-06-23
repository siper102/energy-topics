import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useSetups } from "../context/SetupContext";

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setups, activeSetup, setActiveSetupId } = useSetups();

  return (
    <nav
      style={{
        background: "#fff",
        borderBottom: "1px solid #e2e8f0",
        padding: "0.75rem 2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "2.5rem" }}>
        <div
          onClick={() => navigate("/")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            fontSize: "1.4rem",
            fontWeight: "800",
            color: "#1a202c",
            cursor: "pointer",
            letterSpacing: "-0.02em",
          }}
        >
          <span style={{ fontSize: "1.6rem" }}>🔋</span>{" "}
          <span>
            Battery<span style={{ color: "#3182ce" }}>Opt</span>
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            onClick={() => navigate("/")}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              background: location.pathname === "/" ? "#ebf8ff" : "transparent",
              border: "none",
              color: location.pathname === "/" ? "#2b6cb0" : "#4a5568",
              fontWeight: "600",
              cursor: "pointer",
              fontSize: "0.95rem",
              transition: "all 0.2s",
            }}
          >
            Operations
          </button>
          <button
            onClick={() => navigate("/global")}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              background:
                location.pathname === "/global" ? "#ebf8ff" : "transparent",
              border: "none",
              color: location.pathname === "/global" ? "#2b6cb0" : "#4a5568",
              fontWeight: "600",
              cursor: "pointer",
              fontSize: "0.95rem",
              transition: "all 0.2s",
            }}
          >
            Global Dashboard
          </button>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div
          style={{
            position: "relative",
            display: "flex",
            alignItems: "center",
          }}
        >
          <select
            value={activeSetup?.id || ""}
            onChange={(e) => setActiveSetupId(parseInt(e.target.value))}
            style={{
              padding: "0.6rem 1rem 0.6rem 1rem",
              borderRadius: "10px",
              border: "1px solid #cbd5e0",
              background: "#f7fafc",
              color: "#2d3748",
              fontWeight: "700",
              outline: "none",
              cursor: "pointer",
              fontSize: "0.9rem",
              minWidth: "200px",
              boxShadow: "inset 0 1px 2px rgba(0,0,0,0.05)",
            }}
          >
            {setups.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => alert("Setup Management coming soon!")}
          style={{
            background: "#f7fafc",
            border: "1px solid #cbd5e0",
            borderRadius: "10px",
            width: "38px",
            height: "38px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            fontSize: "1.1rem",
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = "#edf2f7")}
          onMouseOut={(e) => (e.currentTarget.style.background = "#f7fafc")}
          title="Manage Setups"
        >
          ⚙️
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
