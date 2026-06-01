import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Jobs from './pages/Jobs';

const App: React.FC = () => {
  return (
    <Router>
      <div style={{ fontFamily: 'sans-serif', background: '#f5f7f9', minHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<Jobs />} />
          <Route path="*" element={<Jobs />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
