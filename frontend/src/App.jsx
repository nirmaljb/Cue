import { PatientMode } from './pages/PatientMode';
import { CaregiverMode } from './pages/CaregiverMode';
import './App.css';

function App() {
  // Simple routing based on pathname
  const path = window.location.pathname;

  if (path === '/caregiver') {
    return <CaregiverMode />;
  }

  return <PatientMode />;
}

export default App;
