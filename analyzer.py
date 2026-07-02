import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


class Analyzer:

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.model = LinearRegression()

    def load_data(self):
        self.df = pd.read_csv(self.csv_path)

        self.df["price"] = pd.to_numeric(self.df["price"], errors="coerce")
        self.df = self.df.dropna(subset=["price"])

        self.df["engagement"] = (
            self.df["likes"] + self.df["comments"]
        )

    def analyze(self):
        X = self.df[["price"]]
        y = self.df["engagement"]

        self.model.fit(X, y)

        print(f"Slope: {self.model.coef_[0]:.4f}")
        print(f"Intercept: {self.model.intercept_:.4f}")
        print(f"R² Score: {self.model.score(X, y):.4f}")

        if self.model.coef_[0] > 0:
            print("Conclusion: Higher-priced products tend to receive more engagement.")
        elif self.model.coef_[0] < 0:
            print("Conclusion: Higher-priced products tend to receive less engagement.")
        else:
            print("Conclusion: No relationship found.")

    def plot(self):
        self.df = self.df.sort_values("price")

        X = self.df[["price"]]
        predictions = self.model.predict(X)

        plt.figure(figsize=(8, 5))
        plt.scatter(self.df["price"], self.df["engagement"], label="Products")
        plt.plot(self.df["price"], predictions, color="red", label="Regression")

        plt.title("Price vs Engagement")
        plt.xlabel("Price")
        plt.ylabel("Engagement")
        plt.legend()

        plt.show()

    def run(self):
        self.load_data()
        self.analyze()
        self.plot()