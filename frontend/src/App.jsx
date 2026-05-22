import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ErrorBoundary from "./components/common/ErrorBoundary.jsx";
import TacticalLayout from "./components/layout/TacticalLayout.jsx";

const Assessment = lazy(() => import("./pages/Assessment.jsx"));
const Dashboard = lazy(() => import("./pages/Dashboard.jsx"));
const Landing = lazy(() => import("./pages/Landing.jsx"));
const Results = lazy(() => import("./pages/Results.jsx"));

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<div className="route-loading">Loading interface...</div>}>
        <Routes>
          <Route element={<TacticalLayout />}>
            <Route index element={<Landing />} />
            <Route path="assessment" element={<Assessment />} />
            <Route path="results" element={<Results />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
