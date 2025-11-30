import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import { Portfolio } from '@/pages/Portfolio';
import { NotFound } from '@/pages/NotFound';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

