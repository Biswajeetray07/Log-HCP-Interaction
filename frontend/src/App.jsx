import React from 'react';
import Navbar from './components/layout/Navbar';
import Home from './pages/Home';

function App() {
  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200 selection:bg-blue-500/30">
      <Navbar />
      <main>
        <Home />
      </main>
    </div>
  );
}

export default App;
