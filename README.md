Global Chocolate Sales Dashboard
Overview
The Global Chocolate Sales Dashboard is a data visualization project designed to analyze and present sales performance data for a fictional chocolate company, "Awesome Chocolates." This project leverages Power BI to create an interactive and insightful dashboard, providing key metrics and trends to support data-driven decision-making for stakeholders. The dashboard visualizes sales data across products, regions, and salespeople, offering a comprehensive view of the company's performance.
Features

Interactive Visualizations: Dynamic charts and graphs to explore sales trends, product performance, and regional sales.
Key Metrics: Displays critical KPIs such as total sales, top-performing products, and salesperson contributions.
Geographical Insights: Sales data broken down by region, country, and city for granular analysis.
Product Analysis: Detailed insights into product categories and their sales performance.
User-Friendly Interface: Intuitive design for easy navigation and data exploration.

Dataset
The dashboard is built using the "Awesome Chocolates" dataset, which includes the following tables:

Geo: Contains geographical information (e.g., region, country, city).
People: Details about salespeople involved in transactions.
Products: Information on chocolate products, including product codes and categories.
Sales: Transactional data linking products, salespeople, and geographical regions.

The dataset is stored in a MySQL database and queried using SQL to extract relevant data for visualization in Power BI.
Prerequisites
To run and explore this dashboard, you will need:

Power BI Desktop: For viewing and editing the .pbix file.
MySQL: For managing and querying the dataset.
MySQL Connector: To connect Power BI to the MySQL database.
Basic SQL Knowledge: For modifying queries to filter data (e.g., by product code).
DAX Knowledge: For creating calculated measures in Power BI (optional for advanced customization).

Installation and Setup

Clone the Repository:git clone https://github.com/masrafulislam/Global-Chocolate-Sales-Dashboard.git


Set Up the MySQL Database:
Download the "Awesome Chocolates" dataset (link to dataset if available, or include in the repository).
Import the dataset into a MySQL database running on localhost:3306.


Open the Power BI File:
Launch Power BI Desktop.
Open the Sales Report.pbix file located in the repository.


Connect to the Database:
Ensure the MySQL server is running.
Update the data source settings in Power BI to connect to your MySQL database.


Customize the Dashboard:
Modify the SQL query in Power BI to filter data (e.g., by specific product codes).
Update parameters in Power BI for dynamic data filtering.


Refresh the Data:
Click the "Refresh" button in Power BI to update the dashboard with the latest data.



Usage

Explore the Dashboard: Use the interactive charts to analyze sales by region, product, or salesperson.
Filter Data: Apply filters in Power BI to focus on specific products, regions, or time periods.
Generate Insights: Use the visualizations to identify top-performing products, underperforming regions, or high-achieving salespeople.
Export Reports: Export visualizations or data from Power BI for presentations or further analysis.

Project Structure
Global-Chocolate-Sales-Dashboard/
├── Sales Report.pbix          # Power BI file containing the dashboard
├── dataset/                   # Folder for the Awesome Chocolates dataset (if included)
├── queries/                   # SQL queries for data extraction (optional)
├── README.md                  # This file

Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes and commit (git commit -m "Add feature").
Push to the branch (git push origin feature-branch).
Open a pull request.

Please ensure your changes align with the project's goals and follow best practices for Power BI and SQL development.
License
This project is licensed under the MIT License. See the LICENSE file for details.
Acknowledgements

The "Awesome Chocolates" dataset used in this project is sourced from [dataset source, if applicable].
Built with Power BI and MySQL for data visualization and management.

Contact
For questions or suggestions, please contact Masraful Islam or open an issue in the repository.
