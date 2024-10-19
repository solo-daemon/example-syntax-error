import ccxt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import time

class CryptoTradingBot:
    def __init__(self, exchange, symbol, timeframe='1h', lstm_units=50, epochs=100, batch_size=32):
        self.exchange = ccxt.exchange(exchange)()
        self.symbol = symbol
        self.timeframe = timeframe
        self.lstm_units = lstm_units
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler = MinMaxScaler()

    def fetch_data(self, limit=1000):
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def prepare_data(self, data, lookback=60):
        scaled_data = self.scaler.fit_transform(data[['close']])
        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])
        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=self.lstm_units, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=self.lstm_units))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_model(self):
        data = self.fetch_data()
        X, y = self.prepare_data(data)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        self.model = self.build_model((X.shape[1], 1))
        self.model.fit(X, y, epochs=self.epochs, batch_size=self.batch_size, verbose=1)

    def predict(self, lookback=60):
        data = self.fetch_data(limit=lookback)
        scaled_data = self.scaler.transform(data[['close']])
        X = scaled_data[-lookback:].reshape((1, lookback, 1))
        prediction = self.model.predict(X)
        return self.scaler.inverse_transform(prediction)[0, 0]

    def execute_trade(self, prediction, threshold=0.01):
        current_price = self.exchange.fetch_ticker(self.symbol)['last']
        if prediction > current_price * (1 + threshold):
            print(f"Placing buy order for {self.symbol}")
            # self.exchange.create_market_buy_order(self.symbol, amount)
        elif prediction < current_price * (1 - threshold):
            print(f"Placing sell order for {self.symbol}")
            # self.exchange.create_market_sell_order(self.symbol, amount)
        else:
            print("No trade executed")

    def run(self):
        self.train_model()
        while True:
            try:
                prediction = self.predict()
                self.execute_trade(prediction)
                time.sleep(3600)  # Wait for 1 hour before next prediction
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    bot = CryptoTradingBot('binance', 'BTC/USDT')
    bot.run()