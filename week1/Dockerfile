FROM python:3.12-slim


WORKDIR /app

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    gcc g++ unixodbc-dev curl gnupg2 apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft package signing key
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# Add Microsoft repo for Debian 12, signed with the key above
RUN curl -sSL https://packages.microsoft.com/config/debian/12/prod.list | \
    sed 's/\[arch=amd64\]/[arch=amd64 signed-by=\/usr\/share\/keyrings\/microsoft-prod.gpg]/' \
    > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC driver
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
