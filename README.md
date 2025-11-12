# 📊 NSE Indices Heatmap Dashboard

An interactive Streamlit web application for visualizing the performance of National Stock Exchange (NSE) indices in India. This dashboard provides a dynamic heatmap of index constituents, real-time market insights powered by Groq AI, and a clear view of market breadth and sector performance.

![Dashboard Screenshot](https://github.com/madhavarapuchandrasekharasrisai/AI-Powered-Stock-Market-Analysis-App/blob/main/dashboard%20screenshot.png)

## ✨ Features

- **Dynamic Heatmaps**: Visualize the performance of stocks within an index. The size of each rectangle can represent either market capitalization or daily percentage change, while the color indicates the stock's price movement (green for gainers, red for losers).
- **Single & Multi-Index Modes**:
  - **Single Index**: Dive deep into a specific index with detailed data, sorting options, and a search filter.
  - **Multi-Index Comparison**: Compare up to three different indices side-by-side to understand market trends at a glance.
- **Real-Time Insights**: Get concise, AI-generated summaries of market performance using the **Groq API**.
- **Market Breadth**: A dedicated pie chart shows the ratio of advancing, declining, and unchanged stocks for a quick overview of market sentiment.
- **Total Market Overview**: For the **NIFTY TOTAL MARKET** index, the dashboard displays key aggregates like total market cap, average P/E ratio, and top gainers/losers.
- **Auto-Refresh**: The dashboard automatically refreshes every 5 minutes to provide the latest data.

## 🚀 How to Run Locally

### Prerequisites

- Python 3.8 or higher
- `pip` (Python package installer)

### Step-by-Step Instructions

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/username/repo-name.git](https://github.com/username/repo-name.git)
    cd repo-name
    ```
    *Replace `username/repo-name` with your actual GitHub username and repository name.*

2.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```
    If you don't have a `requirements.txt` file, you can create one by running:
    ```bash
    pip freeze > requirements.txt
    ```
    Or, you can install the dependencies manually:
    ```bash
    pip install streamlit pandas plotly-express requests streamlit-autorefresh yfinance groq
    ```

3.  **Set up API Keys:**
    The application uses the **Groq API** for AI-powered market insights. You need to provide your API key.

    - Create a `.streamlit` folder in the root of your project.
    - Inside this folder, create a file named `secrets.toml`.
    - Add your Groq API key to this file:
      ```toml
      GROQ_API_KEY="your_groq_api_key_here"
      ```
    - Replace `"your_groq_api_key_here"` with your actual API key obtained from [Groq Console](https://console.groq.com/).

4.  **Run the Streamlit app:**
    ```bash
    streamlit run your_app_name.py
    ```
    *Replace `your_app_name.py` with the name of your main Python script (e.g., `app.py` or `dashboard.py`).*

    This command will start the web server and open the dashboard in your default web browser.

## 🤝 Contributing

Contributions are welcome! If you have suggestions for new features, bug fixes, or improvements, please feel free to open an issue or submit a pull request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a pull request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Disclaimer**: This application is for informational and educational purposes only. It is not financial advice. All data is sourced from NSE India and Yahoo Finance.
