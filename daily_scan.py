import datetime
import pandas as pd
from FinMind.data import DataLoader

def run_smart_scan():
    dl = DataLoader()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 1. 抓取法人數據與行情
        df_inst = dl.taiwan_stock_institutional_investors(
            start_date=(datetime.datetime.now() - datetime.timedelta(days=20)).strftime('%Y-%m-%d'),
            end_date=today
        )
        df_daily = dl.taiwan_stock_daily_last() # 全市場現價與成交量
        df_dividend = dl.taiwan_stock_dividend_result() # 股利數據

        # --- 區塊 A：投信連買掃描 ---
        sitc_df = df_inst[df_inst['name'] == 'Investment_Trust'].sort_values(['stock_id', 'date'], ascending=[True, False])
        active_stocks = df_daily[df_daily['trading_volume'] > 1000]['stock_id'].tolist()
        
        momentum_results = []
        for stock_id, group in sitc_df.groupby('stock_id'):
            if stock_id not in active_stocks: continue
            buys = group['buy'].values
            count = 0
            for b in buys:
                if b > 0: count += 1
                else: break
            if count >= 5:
                momentum_results.append({"股票代號": stock_id, "連買天數": count, "今日買超": int(buys[0])})

        # --- 區塊 B：高殖利率前 50 名 ---
        # 計算每檔股票的最新殖利率
        latest_div = df_dividend.sort_values('date').groupby('stock_id').last()
        df_yield = pd.merge(df_daily[['stock_id', 'close']], latest_div[['stock_id', 'cash_dividend_caption']], on='stock_id')
        
        # 轉為數值並計算百分比 (殖利率 = 現金股利 / 現價)
        df_yield['yield_pct'] = (df_yield['cash_dividend_caption'].astype(float) / df_yield['close']) * 100
        yield_top_50 = df_yield.sort_values('yield_pct', ascending=False).head(50)

        # --- 2. 生成 README 內容 ---
        content = f"# 📈 台股自動化投資儀表板\n\n"
        content += f"> 更新時間: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n"

        content += "## 🔥 投信連續買超 (動能區)\n"
        if momentum_results:
            content += pd.DataFrame(momentum_results).to_markdown(index=False) + "\n\n"
        else:
            content += "📭 今日暫無符合條件標的。\n\n"

        content += "## 💰 高殖利率精選前 50 名 (價值區)\n"
        content += "| 股票代號 | 現價 | 現金股利 | 殖利率 (%) |\n"
        content += "| :--- | :--- | :--- | :--- |\n"
        for _, row in yield_top_50.iterrows():
            content += f"| {row['stock_id']} | {row['close']} | {row['cash_dividend_caption']} | **{row['yield_pct']:.2f}%** |\n"

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    run_smart_scan()