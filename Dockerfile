FROM python:3.13-slim

WORKDIR /app

COPY . /app/

# 1. Install core dependencies, including iODBC, unixODBC-dev, and gnupg.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libiodbc2 \
       unixodbc-dev \
       curl \
       apt-transport-https \
       gnupg \
    && rm -rf /var/lib/apt/lists/*

# --- MODIFIED STEPS TO RELIABLY INSTALL MICROSOFT ODBC DRIVER ---

# 2. Add Microsoft SQL Server ODBC Driver 18
#    2a. Download the key and save it to a location that will be referenced in the source list.
#        The key is saved to /usr/share/keyrings/mssql-keyring.gpg
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/mssql-keyring.gpg

#    2b. Create the source list file manually, explicitly pointing to the key file location (signed-by).
#        This replaces the two failed 'RUN curl' steps.
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/mssql-keyring.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-prod.list

# 3. Update package list and install the ODBC Driver 18
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# --- END OF MODIFIED STEPS ---

# 4. Install Python dependencies
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "wsgi.py"]