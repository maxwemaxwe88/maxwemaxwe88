import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ExchangeCard from './components/ExchangeCard';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      // In development, we need to point to the backend URL.
      // Assuming backend is running on port 8000
      const response = await axios.get('http://localhost:8000/api/data');
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch data. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, []);

  // Group data by exchange
  const groupedData = data.reduce((acc, item) => {
    if (!acc[item.exchange]) {
      acc[item.exchange] = [];
    }
    acc[item.exchange].push(item);
    return acc;
  }, {});

  const exchangeNames = Object.keys(groupedData).sort();

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      <header className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Crypto <span className="text-blue-500">OI Screener</span>
        </h1>
        <div className="text-sm text-gray-400">
           {loading ? 'Fetching...' : `Updated: ${new Date().toLocaleTimeString()}`}
        </div>
      </header>

      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded mb-6">
          {error}
        </div>
      )}

      {loading && data.length === 0 ? (
        <div className="text-center text-gray-500 mt-20">Loading market data...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {exchangeNames.map(name => (
            <ExchangeCard key={name} exchangeName={name} data={groupedData[name]} />
          ))}
          
          {exchangeNames.length === 0 && !loading && (
             <div className="col-span-full text-center text-gray-500">No data available yet. Backend might be warming up.</div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
