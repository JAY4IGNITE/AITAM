import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { Analyze } from './pages/Analyze';
import { InvestigationView } from './pages/InvestigationView';
import { ThreatIntel } from './pages/ThreatIntel';
import { IncidentsQueue } from './components/IncidentsQueue';
import { IncidentDetails } from './components/IncidentDetails';
import { Datasets } from './pages/Datasets';
import { EvaluationRunner } from './pages/EvaluationRunner';
import { EvaluationResults } from './pages/EvaluationResults';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            
            {/* We will route /investigations to a dedicated list page later. For now, redirect to dashboard */}
            <Route path="/investigations" element={<Navigate to="/" replace />} />
            <Route path="/investigations/:id" element={<InvestigationView />} />
            
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/incidents" element={<IncidentsQueue />} />
            <Route path="/incidents/:id" element={<IncidentDetails />} />
            
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/evaluation/run" element={<EvaluationRunner />} />
            <Route path="/evaluation/:id" element={<EvaluationResults />} />
            
            {/* Catch-all for non-implemented routes during hackathon */}
            <Route path="/reports" element={<div className="p-8 text-gray-500">Reports functionality is accessible via individual investigations.</div>} />
            <Route path="/analytics" element={<Navigate to="/" replace />} />
            <Route path="/settings" element={<div className="p-8 text-gray-500">Settings configuration coming soon.</div>} />
          </Routes>
        </AppShell>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
