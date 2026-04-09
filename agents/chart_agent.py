import os
import json
import logging
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import matplotlib
matplotlib.use('Agg')  # ✅ headless mode (no GUI needed)

logging.basicConfig(level=logging.INFO)


class ChartAgent:
    def __init__(self, output_dir: str = "data/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_sentiment_bar_chart(self, sentiment_data: dict) -> str:
        """Bar chart of bullish/bearish/neutral per ticker."""
        tickers = list(sentiment_data.keys())
        bullish  = [sentiment_data[t]["sentiment_percentages"]["bullish"] for t in tickers]
        bearish  = [sentiment_data[t]["sentiment_percentages"]["bearish"] for t in tickers]
        neutral  = [sentiment_data[t]["sentiment_percentages"]["neutral"] for t in tickers]

        x = np.arange(len(tickers))
        width = 0.25

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        bars1 = ax.bar(x - width, bullish, width, label='Bullish',  color='#2ea043', alpha=0.9)
        bars2 = ax.bar(x,         bearish, width, label='Bearish',  color='#da3633', alpha=0.9)
        bars3 = ax.bar(x + width, neutral, width, label='Neutral',  color='#6e7681', alpha=0.9)

        # Value labels on bars
        for bar in bars1 + bars2 + bars3:
            h = bar.get_height()
            if h > 0:
                ax.annotate(f'{h:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom',
                    color='white', fontsize=8)

        ax.set_xlabel('Ticker', color='white', fontsize=12)
        ax.set_ylabel('Percentage (%)', color='white', fontsize=12)
        ax.set_title('Insider Trading Sentiment Analysis\n(Last 7 Days)', 
                     color='white', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tickers, color='white', fontsize=11)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#30363d')
        ax.spines['left'].set_color('#30363d')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.grid(True, color='#21262d', linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        ax.legend(facecolor='#161b22', labelcolor='white', fontsize=10)
        ax.set_ylim(0, 100)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "sentiment_bar.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        logging.info(f"Chart saved: {path}")
        return path

    def generate_sentiment_pie_chart(self, sentiment_data: dict, ticker: str) -> str:
        """Pie chart for a single ticker."""
        if ticker not in sentiment_data:
            raise ValueError(f"Ticker {ticker} not found in sentiment data")

        pct = sentiment_data[ticker]["sentiment_percentages"]
        labels  = ['Bullish', 'Bearish', 'Neutral']
        sizes   = [pct['bullish'], pct['bearish'], pct['neutral']]
        colors  = ['#2ea043', '#da3633', '#6e7681']
        explode = (0.05, 0.05, 0)

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        wedges, texts, autotexts = ax.pie(
            sizes, explode=explode, labels=labels,
            colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=140,
            textprops={'color': 'white', 'fontsize': 12}
        )
        for at in autotexts:
            at.set_color('white')
            at.set_fontweight('bold')

        ax.set_title(f'${ticker} Sentiment Distribution\n(Last 7 Days)',
                     color='white', fontsize=14, fontweight='bold')

        plt.tight_layout()
        path = os.path.join(self.output_dir, f"sentiment_pie_{ticker}.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        logging.info(f"Chart saved: {path}")
        return path

    def generate_insider_trading_chart(self, transactions: list) -> str:
        """Bar chart of total insider trading value per ticker."""
        ticker_totals = {}
        for tx in transactions:
            t = tx.get("ticker", "")
            ticker_totals[t] = ticker_totals.get(t, 0) + tx.get("value", 0)

        # Top 10
        sorted_tickers = sorted(ticker_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        tickers = [t for t, _ in sorted_tickers]
        values  = [v / 1_000_000 for _, v in sorted_tickers]  # in millions

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        colors = ['#f78166' if v > 10 else '#ffa657' if v > 1 else '#3fb950' for v in values]
        bars = ax.bar(tickers, values, color=colors, alpha=0.9, edgecolor='#30363d')

        for bar, val in zip(bars, values):
            ax.annotate(f'${val:.1f}M',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom',
                color='white', fontsize=9, fontweight='bold')

        ax.set_xlabel('Ticker', color='white', fontsize=12)
        ax.set_ylabel('Transaction Value (Millions USD)', color='white', fontsize=12)
        ax.set_title('SEC Insider Trading — Top Transactions\n(Last 7 Days)',
                     color='white', fontsize=14, fontweight='bold')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#30363d')
        ax.spines['left'].set_color('#30363d')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.grid(True, color='#21262d', linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)

        # Legend
        high   = mpatches.Patch(color='#f78166', label='>$10M (High)')
        medium = mpatches.Patch(color='#ffa657', label='>$1M (Medium)')
        low    = mpatches.Patch(color='#3fb950', label='<$1M (Low)')
        ax.legend(handles=[high, medium, low],
                  facecolor='#161b22', labelcolor='white', fontsize=10)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "insider_trading.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        logging.info(f"Chart saved: {path}")
        return path

    def generate_comparison_chart(self, sentiment_data: dict) -> str:
        """Radar/spider chart comparing all tickers."""
        tickers = list(sentiment_data.keys())
        if not tickers:
            raise ValueError("No sentiment data available")

        categories = ['Bullish', 'Bearish', 'Neutral']
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        colors = ['#2ea043', '#da3633', '#ffa657', '#58a6ff', '#bc8cff']

        for idx, ticker in enumerate(tickers):
            pct = sentiment_data[ticker]["sentiment_percentages"]
            values = [pct['bullish'], pct['bearish'], pct['neutral']]
            values += values[:1]
            color = colors[idx % len(colors)]
            ax.plot(angles, values, 'o-', linewidth=2, color=color, label=f'${ticker}')
            ax.fill(angles, values, alpha=0.1, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, color='white', fontsize=12)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'],
                           color='#6e7681', fontsize=8)
        ax.grid(color='#30363d', linestyle='--', alpha=0.7)
        ax.spines['polar'].set_color('#30363d')
        ax.set_title('Sentiment Comparison — All Tickers',
                     color='white', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
                  facecolor='#161b22', labelcolor='white', fontsize=10)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "sentiment_comparison.png")
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        logging.info(f"Chart saved: {path}")
        return path
