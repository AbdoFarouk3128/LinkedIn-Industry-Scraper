# LinkedIn Company Scraper

A Python script that automates LinkedIn login, searches for companies by name, and scrapes key data like company name and industry.

---

## ✨ Features

- ✅ **Automated Login** using Selenium and your LinkedIn credentials  
- 🔍 **Search by Company Name** on LinkedIn  
- 🏷️ **Scrapes Company Name and Industry**  
- 🗕️ **Reads Input from Excel** (`input/company_names.xlsx`)  
- 📄 **Outputs Results to Excel** (`output/industry_data.xlsx`)  
- ⚙️ **Configurable & Modular**  

---

## 🔧 Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/AbdoFarouk3128/LinkedIn-Industry-Scraper.git
   cd LinkedIn-Industry-Scraper

2. **Install required packages:**:
    ```bash
    pip install -r requirements.txt

---

## 🔐 Configuration

1. Create a file named config.py in the root directory.

2. **Add your LinkedIn login credentials:**:
    LINKEDIN_EMAIL = "your_email@example.com"
    LINKEDIN_PASSWORD = "your_password"

- ⚠️ Never share or commit your credentials to GitHub!

---

## 🗒️ Input File Format

- Input File: input/company_names.xlsx

- **Sheet Format**:
    First row must contain the header: Company Name
    Below that, add each company name to be searched

- **Example**:

    - Company Name
    - OpenAI
    - Google
    - Microsoft

---

## Accuracy & Limitations

- Accuracy: High if LinkedIn layout is unchanged.

- Limitations:

    - May not work on private or incomplete pages

    - Manual input may be needed if 2FA is enabled

    - Use responsibly to avoid detection or rate-limiting

    - Add delays or use proxies for bulk scraping