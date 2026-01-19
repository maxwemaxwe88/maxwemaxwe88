#!/usr/bin/env python3
"""
Coinglass Open Interest Screener - Web Interface
"""
from flask import Flask, render_template, jsonify, request
from src.screener import OpenInterestScreener, SortBy
from src.config import Config
import json

app = Flask(__name__)

# Initialize screener
screener = OpenInterestScreener()


@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html")


@app.route("/api/oi")
def get_oi_data():
    """
    API endpoint for open interest data
    
    Query params:
    - limit: Number of results (default 50)
    - sort: Sort field (oi, oi_1h, oi_4h, oi_24h, price, volume)
    - order: asc or desc (default desc)
    - min_oi: Minimum OI in USD
    - exchange: Filter by exchange
    """
    try:
        limit = int(request.args.get("limit", 50))
        sort = request.args.get("sort", "oi")
        order = request.args.get("order", "desc")
        min_oi = float(request.args.get("min_oi", 1000000))
        exchange = request.args.get("exchange")
        
        sort_map = {
            "oi": SortBy.OI_VALUE,
            "oi_1h": SortBy.OI_CHANGE_1H,
            "oi_4h": SortBy.OI_CHANGE_4H,
            "oi_24h": SortBy.OI_CHANGE_24H,
            "price": SortBy.PRICE,
            "volume": SortBy.VOLUME_24H
        }
        
        result = screener.screen(
            sort_by=sort_map.get(sort, SortBy.OI_VALUE),
            ascending=(order == "asc"),
            limit=limit,
            exchange=exchange if exchange else None,
            min_oi_usd=min_oi
        )
        
        if result.data.empty:
            return jsonify({"data": [], "total": 0, "filtered": 0})
        
        # Convert to list of dicts
        data = result.data.to_dict(orient="records")
        
        return jsonify({
            "data": data,
            "total": result.total_count,
            "filtered": result.filtered_count,
            "timestamp": result.timestamp
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gainers")
def get_gainers():
    """Get top OI gainers"""
    try:
        timeframe = request.args.get("timeframe", "24h")
        limit = int(request.args.get("limit", 20))
        min_oi = float(request.args.get("min_oi", 1000000))
        
        result = screener.get_top_oi_gainers(
            timeframe=timeframe,
            limit=limit,
            min_oi_usd=min_oi
        )
        
        if result.data.empty:
            return jsonify({"data": []})
        
        return jsonify({
            "data": result.data.to_dict(orient="records"),
            "timeframe": timeframe
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/losers")
def get_losers():
    """Get top OI losers"""
    try:
        timeframe = request.args.get("timeframe", "24h")
        limit = int(request.args.get("limit", 20))
        min_oi = float(request.args.get("min_oi", 1000000))
        
        result = screener.get_top_oi_losers(
            timeframe=timeframe,
            limit=limit,
            min_oi_usd=min_oi
        )
        
        if result.data.empty:
            return jsonify({"data": []})
        
        return jsonify({
            "data": result.data.to_dict(orient="records"),
            "timeframe": timeframe
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/unusual")
def get_unusual():
    """Get unusual OI activity"""
    try:
        threshold = float(request.args.get("threshold", 5.0))
        limit = int(request.args.get("limit", 20))
        min_oi = float(request.args.get("min_oi", 500000))
        
        result = screener.get_unusual_activity(
            oi_change_threshold=threshold,
            limit=limit,
            min_oi_usd=min_oi
        )
        
        if result.data.empty:
            return jsonify({"data": []})
        
        return jsonify({
            "data": result.data.to_dict(orient="records"),
            "threshold": threshold
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/divergence")
def get_divergence():
    """Get OI/Price divergence signals"""
    try:
        limit = int(request.args.get("limit", 20))
        min_oi = float(request.args.get("min_oi", 1000000))
        
        result = screener.get_divergence_signals(
            limit=limit,
            min_oi_usd=min_oi
        )
        
        if result.data.empty:
            return jsonify({"data": []})
        
        return jsonify({
            "data": result.data.to_dict(orient="records")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary")
def get_summary():
    """Get market summary statistics"""
    try:
        stats = screener.get_summary_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/exchanges")
def get_exchanges():
    """Get list of supported exchanges"""
    return jsonify({"exchanges": Config.SUPPORTED_EXCHANGES})


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "api_key_configured": Config.is_api_key_set()
    })


if __name__ == "__main__":
    print("\n🚀 Starting Coinglass Open Interest Screener")
    print("📊 Dashboard available at http://localhost:5000")
    print("📡 API endpoints at http://localhost:5000/api/\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
