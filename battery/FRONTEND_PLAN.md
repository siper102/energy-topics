# Plan: Step-by-Step Frontend Two-View Architecture

## Objective
Refactor the React frontend to feature two distinct views (Dashboard and Jobs) and add required backend endpoints, executing in small, verifiable steps to ensure stability.

## Step-by-Step Execution Plan

### Step 1: Backend Stability & Data Endpoint
**Goal:** Fix known crashes and prepare the backend to serve dashboard data.
1.  **Fix Optimization Crash:** Add safety checks in `optimization_service/src/optimization/database_connector.py` to prevent crashes when the database is empty (throwing a clean `ValueError` instead).
2.  **Create Data Endpoint:** Add `GET /dashboard-data` in `core_api/src/api/data_routes.py` to fetch and return historical `sensor_telemetry` and `dispatch_plans`.
3.  **Verification:** Restart the backend services. Manually hit the `/dashboard-data` endpoint to ensure it returns data. Verify the optimization endpoint fails gracefully if the DB is empty.

### Step 2: Frontend Routing & Layout Scaffold
**Goal:** Set up the basic multi-page structure without touching existing logic yet.
1.  **Install Dependencies:** Run `npm install react-router-dom` in the `frontend` container.
2.  **Create Pages:** Create empty placeholder files: `src/pages/Dashboard.tsx` and `src/pages/Jobs.tsx`.
3.  **Setup Routing:** Update `src/main.tsx` and `App.tsx` to configure `BrowserRouter` and routes.
4.  **Add Navigation:** Create a simple `Navbar` component.
5.  **Verification:** Verify that clicking navigation links changes the URL and displays placeholder pages.

### Step 3: Migrate Jobs View
**Goal:** Move the existing trigger functionality into its dedicated page.
1.  **Refactor:** Move all the existing state and UI code from the old `App.tsx` into `src/pages/Jobs.tsx`.
2.  **Verification:** Test the "Trigger Ingestion" and "Run Optimization" buttons in the new `/jobs` view.

### Step 4: Implement Dashboard View
**Goal:** Fetch data from the backend and visualize it using charts.
1.  **Install Charting:** Run `npm install recharts` in the `frontend` container.
2.  **Fetch Data:** Add logic in `Dashboard.tsx` to call the new `/dashboard-data` endpoint.
3.  **Build Charts:** Implement Recharts components.
4.  **Verification:** Verify charts populate correctly after running ingestion and optimization.

## Rules of Engagement
- I will execute **one step at a time**.
- After completing a step, I will wait for you to test and confirm it works before starting the next step.
