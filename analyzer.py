import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Read the CSV file
df = pd.read_csv("data/scraped_products.csv")

# Clean the data
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df = df.dropna(subset=["price"])

# Create engagement column
df["engagement"] = df["likes"] + df["comments"]

# Independent variable (Price)
X = df[["price"]]

# Dependent variable (Engagement)
y = df["engagement"]

# Train the linear regression model
model = LinearRegression()
model.fit(X, y)

# Print results
print(f"Slope: {model.coef_[0]:.4f}")
print(f"Intercept: {model.intercept_:.4f}")
print(f"R² Score: {model.score(X, y):.4f}")

# Print a simple conclusion
if model.coef_[0] > 0:
    print("Conclusion: Higher-priced products tend to receive more engagement.")
elif model.coef_[0] < 0:
    print("Conclusion: Higher-priced products tend to receive less engagement.")
else:
    print("Conclusion: No relationship between price and engagement.")

# Sort data so the regression line looks smooth
df = df.sort_values("price")
X = df[["price"]]

# Predict engagement
predictions = model.predict(X)

# Plot
plt.figure(figsize=(8, 5))
plt.scatter(df["price"], df["engagement"], label="Products")
plt.plot(df["price"], predictions, color="red", label="Regression Line")

plt.title("Price vs Engagement")
plt.xlabel("Price")
plt.ylabel("Engagement (Likes + Comments)")
plt.legend()

plt.show()