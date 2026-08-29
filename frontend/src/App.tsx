import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { Analyze } from './pages/Analyze';
import { EmailScanner } from './pages/EmailScanner';
import { InvestigationsList } from './pages/InvestigationsList';
import { InvestigationView } from './pages/InvestigationView';
import { ThreatIntel } from './pages/ThreatIntel';
import { IncidentsQueue } from './components/IncidentsQueue';
import { IncidentDetails } from './components/IncidentDetails';
import { Datasets } from './pages/Datasets';
import { EvaluationRunner } from './pages/EvaluationRunner';
import { EvaluationResults } from './pages/EvaluationResults';
import { Reports } from './pages/Reports';
import { Education } from './pages/Education';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/email-scanner" element={<EmailScanner />} />
            
            <Route path="/investigations" element={<InvestigationsList />} />
            <Route path="/investigations/:id" element={<InvestigationView />} />
            
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/incidents" element={<IncidentsQueue />} />
            <Route path="/incidents/:id" element={<IncidentDetails />} />
            
            <Route path="/reports" element={<Reports />} />
            <Route path="/education" element={<Education />} />
            <Route path="/settings" element={<Settings />} />

            <Route path="/datasets" element={<Datasets />} />
            <Route path="/evaluation/run" element={<EvaluationRunner />} />
            <Route path="/evaluation/:id" element={<EvaluationResults />} />
            
            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
