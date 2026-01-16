/**
 * OI Screener - Frontend Application
 */

class OIScreener {
    constructor() {
        this.ws = null;
        this.data = {};
        this.exchanges = [];
        this.activeExchange = 'all';
        this.sortField = 'oi_change_5m';
        this.sortOrder = 'desc';
        this.minOI = 100000;
        this.searchSymbol = '';
        this.previousData = {};
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.connectWebSocket();
        this.loadSettings();
    }
    
    bindEvents() {
        // Sort controls
        document.getElementById('sortField').addEventListener('change', (e) => {
            this.sortField = e.target.value;
            this.saveSettings();
            this.render();
        });
        
        document.getElementById('sortOrder').addEventListener('change', (e) => {
            this.sortOrder = e.target.value;
            this.saveSettings();
            this.render();
        });
        
        document.getElementById('minOI').addEventListener('input', (e) => {
            this.minOI = parseFloat(e.target.value) || 0;
            this.saveSettings();
            this.render();
        });
        
        document.getElementById('searchSymbol').addEventListener('input', (e) => {
            this.searchSymbol = e.target.value.toUpperCase();
            this.render();
        });
        
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.fetchData();
        });
    }
    
    loadSettings() {
        const settings = localStorage.getItem('oi_screener_settings');
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                this.sortField = parsed.sortField || 'oi_change_5m';
                this.sortOrder = parsed.sortOrder || 'desc';
                this.minOI = parsed.minOI || 100000;
                
                document.getElementById('sortField').value = this.sortField;
                document.getElementById('sortOrder').value = this.sortOrder;
                document.getElementById('minOI').value = this.minOI;
            } catch (e) {
                console.error('Failed to load settings:', e);
            }
        }
    }
    
    saveSettings() {
        localStorage.setItem('oi_screener_settings', JSON.stringify({
            sortField: this.sortField,
            sortOrder: this.sortOrder,
            minOI: this.minOI
        }));
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateStatus('connected', 'Подключено');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (e) {
                // Handle ping/pong
                if (event.data === 'ping') {
                    this.ws.send('pong');
                }
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('disconnected', 'Ошибка');
        };
        
        this.ws.onclose = () => {
            this.updateStatus('disconnected', 'Отключено');
            // Reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        // Keep alive
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 25000);
    }
    
    handleMessage(message) {
        if (message.type === 'initial' || message.type === 'update') {
            this.previousData = { ...this.data };
            this.data = message.data;
            
            if (message.exchanges) {
                this.exchanges = message.exchanges;
                this.renderTabs();
            }
            
            this.updateLastUpdate(message.timestamp);
            this.render();
        }
    }
    
    updateStatus(status, text) {
        const dot = document.getElementById('connectionStatus');
        const statusText = document.getElementById('statusText');
        
        dot.className = 'status-dot ' + status;
        statusText.textContent = text;
    }
    
    updateLastUpdate(timestamp) {
        const date = new Date(timestamp * 1000);
        const time = date.toLocaleTimeString('ru-RU');
        document.getElementById('lastUpdate').textContent = time;
    }
    
    async fetchData() {
        try {
            const response = await fetch('/api/oi');
            const result = await response.json();
            this.previousData = { ...this.data };
            this.data = result.data;
            this.updateLastUpdate(result.timestamp);
            this.render();
        } catch (e) {
            console.error('Failed to fetch data:', e);
        }
    }
    
    renderTabs() {
        const tabsContainer = document.getElementById('exchangeTabs');
        
        let html = '<button class="tab-btn active" data-exchange="all">Все биржи</button>';
        
        for (const exchange of this.exchanges) {
            html += `<button class="tab-btn" data-exchange="${exchange.name}">${exchange.display_name}</button>`;
        }
        
        tabsContainer.innerHTML = html;
        
        // Bind tab events
        tabsContainer.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.activeExchange = e.target.dataset.exchange;
                this.render();
            });
        });
    }
    
    filterAndSortData(data) {
        let filtered = data.filter(item => {
            // Filter by minimum OI
            if (item.oi_value < this.minOI) return false;
            
            // Filter by search
            if (this.searchSymbol && !item.symbol.includes(this.searchSymbol)) {
                return false;
            }
            
            return true;
        });
        
        // Sort
        filtered.sort((a, b) => {
            const aVal = a[this.sortField] || 0;
            const bVal = b[this.sortField] || 0;
            
            if (this.sortOrder === 'asc') {
                return aVal - bVal;
            }
            return bVal - aVal;
        });
        
        return filtered;
    }
    
    render() {
        if (this.activeExchange === 'all') {
            this.renderGrid();
        } else {
            this.renderSingleExchange();
        }
    }
    
    renderGrid() {
        document.getElementById('exchangeGrid').classList.remove('hidden');
        document.getElementById('singleView').classList.add('hidden');
        
        const container = document.getElementById('exchangeGrid');
        
        if (Object.keys(this.data).length === 0) {
            container.innerHTML = '<div class="loading">Загрузка данных</div>';
            return;
        }
        
        let html = '';
        
        for (const [exchangeName, exchangeData] of Object.entries(this.data)) {
            const exchange = this.exchanges.find(e => e.name === exchangeName);
            const displayName = exchange ? exchange.display_name : exchangeName;
            const filtered = this.filterAndSortData(exchangeData);
            
            html += this.renderExchangePanel(exchangeName, displayName, filtered);
        }
        
        container.innerHTML = html;
        
        // Bind table header sort events
        container.querySelectorAll('.oi-table th[data-sort]').forEach(th => {
            th.addEventListener('click', (e) => {
                const field = e.target.dataset.sort;
                if (this.sortField === field) {
                    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sortField = field;
                    this.sortOrder = 'desc';
                }
                document.getElementById('sortField').value = this.sortField;
                document.getElementById('sortOrder').value = this.sortOrder;
                this.saveSettings();
                this.render();
            });
        });
    }
    
    renderSingleExchange() {
        document.getElementById('exchangeGrid').classList.add('hidden');
        document.getElementById('singleView').classList.remove('hidden');
        
        const container = document.getElementById('singleView');
        const exchangeData = this.data[this.activeExchange] || [];
        const exchange = this.exchanges.find(e => e.name === this.activeExchange);
        const displayName = exchange ? exchange.display_name : this.activeExchange;
        const filtered = this.filterAndSortData(exchangeData);
        
        container.innerHTML = `
            <div class="single-table-container">
                ${this.renderExchangePanel(this.activeExchange, displayName, filtered, true)}
            </div>
        `;
        
        // Bind table header sort events
        container.querySelectorAll('.oi-table th[data-sort]').forEach(th => {
            th.addEventListener('click', (e) => {
                const field = e.target.dataset.sort;
                if (this.sortField === field) {
                    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sortField = field;
                    this.sortOrder = 'desc';
                }
                document.getElementById('sortField').value = this.sortField;
                document.getElementById('sortOrder').value = this.sortOrder;
                this.saveSettings();
                this.render();
            });
        });
    }
    
    renderExchangePanel(exchangeName, displayName, data, fullSize = false) {
        const iconLetter = displayName.charAt(0).toUpperCase();
        
        return `
            <div class="exchange-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <div class="exchange-icon">${iconLetter}</div>
                        ${displayName}
                    </div>
                    <span class="panel-count">${data.length} пар</span>
                </div>
                <div class="table-container">
                    ${data.length > 0 ? this.renderTable(data, exchangeName) : '<div class="no-data">Нет данных</div>'}
                </div>
            </div>
        `;
    }
    
    renderTable(data, exchangeName) {
        const getSortClass = (field) => this.sortField === field ? 'sorted' : '';
        
        let html = `
            <table class="oi-table">
                <thead>
                    <tr>
                        <th data-sort="symbol">Символ</th>
                        <th data-sort="price" class="${getSortClass('price')}">Цена</th>
                        <th data-sort="oi_change_5m" class="${getSortClass('oi_change_5m')}">OI 5м%</th>
                        <th data-sort="oi_change_1h" class="${getSortClass('oi_change_1h')}">OI 1ч%</th>
                        <th data-sort="oi_change_24h" class="${getSortClass('oi_change_24h')}">OI 24ч%</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        for (const item of data.slice(0, 50)) { // Limit to 50 rows per panel
            const prevExchangeData = this.previousData[exchangeName] || [];
            const prevItem = prevExchangeData.find(p => p.symbol === item.symbol);
            const isUpdated = prevItem && (
                prevItem.oi_change_5m !== item.oi_change_5m ||
                prevItem.price !== item.price
            );
            
            html += `
                <tr class="${isUpdated ? 'row-updated' : ''}">
                    <td>
                        <div class="symbol-cell">
                            <div class="symbol-icon">${item.symbol.charAt(0)}</div>
                            ${item.symbol}
                        </div>
                    </td>
                    <td class="price-cell">${this.formatPrice(item.price)}</td>
                    <td><span class="change-cell ${this.getChangeClass(item.oi_change_5m)}">${this.formatPercent(item.oi_change_5m)}</span></td>
                    <td><span class="change-cell ${this.getChangeClass(item.oi_change_1h)}">${this.formatPercent(item.oi_change_1h)}</span></td>
                    <td><span class="change-cell ${this.getChangeClass(item.oi_change_24h)}">${this.formatPercent(item.oi_change_24h)}</span></td>
                </tr>
            `;
        }
        
        html += '</tbody></table>';
        return html;
    }
    
    formatPrice(price) {
        if (price === 0) return '$0';
        if (price < 0.0001) return '$' + price.toExponential(2);
        if (price < 0.01) return '$' + price.toFixed(6);
        if (price < 1) return '$' + price.toFixed(4);
        if (price < 100) return '$' + price.toFixed(2);
        return '$' + price.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }
    
    formatPercent(value) {
        if (value === 0 || value === undefined || value === null) return '0.00%';
        const sign = value > 0 ? '+' : '';
        return sign + value.toFixed(2) + '%';
    }
    
    formatOI(value) {
        if (value >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B';
        if (value >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M';
        if (value >= 1e3) return '$' + (value / 1e3).toFixed(2) + 'K';
        return '$' + value.toFixed(2);
    }
    
    getChangeClass(value) {
        if (value > 0) return 'change-positive';
        if (value < 0) return 'change-negative';
        return 'change-neutral';
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.oiScreener = new OIScreener();
});
