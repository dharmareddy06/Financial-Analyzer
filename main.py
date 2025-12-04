import pandas as pd
import requests
from sqlalchemy import create_engine, text
import mysql.connector
from mysql.connector import Error
import numpy as np
from datetime import datetime
import json

class FinancialAnalyzer:
    def __init__(self):
        self.api_key = "YOUR_API_KEY"
        self.base_url = "YOUR_API_ENDPOINT"
        self.db_config = {
            'host': 'localhost',
            'database': 'financial_analysis_db',
            'user': 'root',
            'password': 'your_password'
        }
        self.engine = self.create_db_connection()
        
    def create_db_connection(self):
        try:
            connection_string = f"mysql+mysqlconnector://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}/{self.db_config['database']}"
            engine = create_engine(connection_string)
            print("MySQL Database connection successful")
            return engine
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")
            return None

    def safe_float_conversion(self, value):
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def fetch_company_data(self, company_id):
        params = {
            'id': company_id,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {company_id}: {e}")
            return None

    def calculate_growth_metrics(self, data_list, value_key):
        if not data_list or len(data_list) < 2:
            return 0
            
        recent_value = self.safe_float_conversion(data_list[0].get(value_key))
        previous_value = self.safe_float_conversion(data_list[1].get(value_key))
        
        if previous_value == 0:
            return 0
            
        return ((recent_value - previous_value) / previous_value) * 100

    def calculate_average_growth(self, data_list, value_key, years=5):
        if not data_list or len(data_list) < years:
            return 0
            
        growth_rates = []
        for i in range(min(years, len(data_list)-1)):
            current = self.safe_float_conversion(data_list[i].get(value_key))
            previous = self.safe_float_conversion(data_list[i+1].get(value_key))
            
            if previous != 0:
                growth_rate = ((current - previous) / previous) * 100
                growth_rates.append(growth_rate)
                
        return np.mean(growth_rates) if growth_rates else 0

    def calculate_median_growth(self, data_list, value_key, years=10):
        if not data_list or len(data_list) < years:
            return 0
            
        growth_rates = []
        for i in range(min(years, len(data_list)-1)):
            current = self.safe_float_conversion(data_list[i].get(value_key))
            previous = self.safe_float_conversion(data_list[i+1].get(value_key))
            
            if previous != 0:
                growth_rate = ((current - previous) / previous) * 100
                growth_rates.append(growth_rate)
                
        return np.median(growth_rates) if growth_rates else 0

    def analyze_financials(self, company_data):
        pros = []
        cons = []
        
        balance_sheet = company_data.get('data', {}).get('balancesheet', [])
        profit_loss = company_data.get('data', {}).get('profitandloss', [])
        cash_flow = company_data.get('data', {}).get('cashflow', [])
        
        balance_sheet.sort(key=lambda x: x.get('year', ''), reverse=True)
        profit_loss.sort(key=lambda x: x.get('year', ''), reverse=True)
        cash_flow.sort(key=lambda x: x.get('year', ''), reverse=True)
        
        if balance_sheet:
            recent_borrowings = self.safe_float_conversion(balance_sheet[0].get('borrowings'))
            if recent_borrowings == 0:
                pros.append("Company is almost debt-free")
            else:
                if len(balance_sheet) > 1:
                    previous_borrowings = self.safe_float_conversion(balance_sheet[1].get('borrowings'))
                    if recent_borrowings < previous_borrowings:
                        debt_reduction = ((previous_borrowings - recent_borrowings) / previous_borrowings) * 100
                        if debt_reduction > 10:
                            pros.append(f"Company has reduced debt by {debt_reduction:.1f}%")
        
        if profit_loss and balance_sheet:
            roe_values = []
            for i in range(min(3, len(profit_loss))):
                net_profit = self.safe_float_conversion(profit_loss[i].get('net_profit'))
                equity = self.safe_float_conversion(balance_sheet[i].get('reserves')) + self.safe_float_conversion(balance_sheet[i].get('equity_capital'))
                if equity > 0:
                    roe = (net_profit / equity) * 100
                    roe_values.append(roe)
            
            if roe_values:
                avg_roe = np.mean(roe_values)
                if avg_roe > 10:
                    pros.append(f"Company has a good return on equity (ROE) track record: 3 Years ROE {avg_roe:.1f}%")
                else:
                    cons.append(f"Company has a low return on equity of {avg_roe:.2f}% over last 3 years")
        
        if profit_loss:
            recent_dividend = profit_loss[0].get('dividend_payout')
            dividend_payout = self.safe_float_conversion(recent_dividend)
            if dividend_payout > 10:
                pros.append(f"Company has been maintaining a healthy dividend payout of {dividend_payout:.1f}%")
            elif dividend_payout == 0:
                cons.append("Company is not paying out dividend")
        
        if profit_loss:
            profit_growth = self.calculate_growth_metrics(profit_loss, 'net_profit')
            if profit_growth > 10:
                pros.append(f"Company has delivered good profit growth of {profit_growth:.1f}%")
            elif profit_growth < 5 and profit_growth != 0:
                cons.append(f"Company has delivered poor profit growth of {profit_growth:.1f}%")
        
        if profit_loss:
            sales_growth = self.calculate_growth_metrics(profit_loss, 'sales')
            if sales_growth < 10 and sales_growth != 0:
                cons.append(f"The company has delivered a poor sales growth of {sales_growth:.1f}% over past year")
            
            sales_growth_5yr = self.calculate_average_growth(profit_loss, 'sales', 5)
            if sales_growth_5yr < 10 and sales_growth_5yr != 0:
                cons.append(f"The company has delivered a poor sales growth of {sales_growth_5yr:.2f}% over past five years")
            
            sales_growth_10yr = self.calculate_median_growth(profit_loss, 'sales', 10)
            if sales_growth_10yr > 10:
                pros.append(f"Company's median sales growth is {sales_growth_10yr:.1f}% of last 10 years")
        
        # Select up to 3 pros and cons
        selected_pros = pros[:3]
        selected_cons = cons[:3]
        
        return selected_pros, selected_cons

    def store_analysis_results(self, company_id, company_name, pros, cons):
        if not self.engine:
            print("Database connection not available")
            return False
            
        try:
            pros_json = json.dumps(pros)
            cons_json = json.dumps(cons)
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            query = text("""
                INSERT INTO ml (company_id, company_name, pros, cons, created_at, updated_at)
                VALUES (:company_id, :company_name, :pros, :cons, :created_at, :updated_at)
                ON DUPLICATE KEY UPDATE
                pros = :pros, cons = :cons, updated_at = :updated_at
            """)
            
            with self.engine.connect() as connection:
                connection.execute(query, {
                    'company_id': company_id,
                    'company_name': company_name,
                    'pros': pros_json,
                    'cons': cons_json,
                    'created_at': created_at,
                    'updated_at': created_at
                })
                connection.commit()
                
            print(f"Analysis results stored for {company_id}")
            return True
            
        except Error as e:
            print(f"Error storing analysis results for {company_id}: {e}")
            return False

    def process_company(self, company_id):
        print(f"Processing {company_id}...")
        
        company_data = self.fetch_company_data(company_id)
        if not company_data:
            print(f"Failed to fetch data for {company_id}")
            return False
        
        company_name = company_data.get('company', {}).get('company_name', 'Unknown')
        
        pros, cons = self.analyze_financials(company_data)
        
        # Display results in terminal
        print(f"\nAnalysis for {company_name} ({company_id}):")
        print("Pros:")
        for pro in pros:
            print(f" {pro}")
        print("Cons:")
        for con in cons:
            print(f" {con}")
        print("-" * 50)
        
        # Store results in database
        success = self.store_analysis_results(company_id, company_name, pros, cons)
        return success

    def process_all_companies(self, company_list):
        success_count = 0
        total_count = len(company_list)
        
        for i, company_id in enumerate(company_list, 1):
            print(f"\nProcessing company {i} of {total_count}")
            if self.process_company(company_id):
                success_count += 1
        
        print(f"\nProcessing complete. Successfully processed {success_count} of {total_count} companies.")

def main():
    analyzer = FinancialAnalyzer()
    
    company_list = ["ABB", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "AMBUJACEM",
                    "APOLLOHOSP", "ASIANPAINT", "ATGL", "AXISBANK", "BAJAJ-AUTO",
                    "BAJAJFINSV", "BAJAJHLDNG", "BAJFINANCE", "BANKBARODA", "BEL",
                    "BHARTIARTL", "BHEL", "BOSCHLTD", "BPCL", "BRITANNIA",
                    "CANBK", "CHOLAFIN", "CIPLA", "COALINDIA", "DABUR",
                    "DLF", "DMART", "DRREDDY", "EICHERMOT", "GAIL",
                    "GODREJCP", "GRASIM", "HAL", "HAVELLS", "HCLTECH",
                    "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
                    "ICICIBANK", "ICICIGI", "ICICIPRULI", "INDIGO", "INDUSINDBK", "INFY",
                    "IOC", "IRCTC", "IRFC", "ITC", "JINDALSTEL", "JIOFIN",
                    "JSWENERGY", "JSWSTEEL", "KOTAKBANK", "LICI", "LODHA", "LT", "LTIM", "M&M", "MARUTI",
                    "MOTHERSON", "NAUKRI", "NESTLEIND", "NHPC", "NTPC", "ONGC", "PFC", "PIDILITIND", "PNB", "POWERGRID",
                    "RECLTD", "RELIANCE", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SUNPHARMA", "TATACONSUM", "TATAMOTORS",
                    "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", "TVSMOTOR", "ULTRACEMCO", "UNIONBANK",
                    "UNITDSPR", "VBL", "VEDL", "WIPRO", "ZOMATO", "ZYDUSLIFE"]
    
    analyzer.process_all_companies(company_list)

if __name__ == "__main__":
    main()