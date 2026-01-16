import React, { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, ArrowRight } from 'lucide-react';

const ExchangeCard = ({ exchangeName, data }) => {
  // Sort data: default by Open Interest Descending
  // The user wants to search for "increase of open interest". 
  // So default sort should probably be by Change (if we had it) or OI.
  // Since we might not have change initially, let's sort by OI Value.
  
  const [sortConfig, setSortConfig] = useState({ key: 'openInterest', direction: 'desc' });

  const sortedData = [...data].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const requestSort = (key) => {
    let direction = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const formatNumber = (num) => {
    if (!num) return '-';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700 flex flex-col h-[500px]">
      <div className="bg-gray-750 p-3 border-b border-gray-700 font-bold text-lg uppercase flex justify-between items-center">
        <span>{exchangeName}</span>
        <span className="text-xs text-gray-400 font-normal">{data.length} pairs</span>
      </div>
      
      <div className="overflow-auto flex-1">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase bg-gray-700 sticky top-0">
            <tr>
              <th className="px-3 py-2 cursor-pointer hover:text-white" onClick={() => requestSort('symbol')}>Symbol</th>
              <th className="px-3 py-2 text-right cursor-pointer hover:text-white" onClick={() => requestSort('price')}>Price</th>
              <th className="px-3 py-2 text-right cursor-pointer hover:text-white" onClick={() => requestSort('openInterest')}>OI (USD)</th>
              <th className="px-3 py-2 text-right cursor-pointer hover:text-white" onClick={() => requestSort('openInterestChange1h')}>Change %</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row) => (
              <tr key={row.symbol} className="border-b border-gray-700 hover:bg-gray-750">
                <td className="px-3 py-2 font-medium text-white">{row.symbol.replace('/USDT', '').replace(':USDT', '')}</td>
                <td className="px-3 py-2 text-right text-gray-300">${parseFloat(row.price).toLocaleString()}</td>
                <td className="px-3 py-2 text-right text-blue-400 font-mono">{formatNumber(row.openInterest)}</td>
                <td className="px-3 py-2 text-right">
                  <span className={`flex items-center justify-end ${row.openInterestChange1h > 0 ? 'text-green-500' : row.openInterestChange1h < 0 ? 'text-red-500' : 'text-gray-400'}`}>
                    {row.openInterestChange1h > 0 ? <ArrowUp size={12} /> : row.openInterestChange1h < 0 ? <ArrowDown size={12} /> : null}
                    {Math.abs(row.openInterestChange1h || 0).toFixed(2)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ExchangeCard;
