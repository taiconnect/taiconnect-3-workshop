FROM postgres:16

# Install pgvector
RUN apt-get update \
  && apt-get install -y postgresql-16-pgvector \
  && rm -rf /var/lib/apt/lists/*

# Copy SQL initialization script
COPY init.sql /docker-entrypoint-initdb.d/