#Build stage
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS builder 

LABEL maintainer="LSEG Developer Relations"
LABEL build_date="2025-10-06"

#Copy requirements.txt
COPY requirements.txt .

# install dependencies to the local user directory (eg. /root/.local)
#RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --no-cache-dir --user -r requirements.txt

# Run stage
FROM python:${PYTHON_VERSION}-alpine3.22
WORKDIR /app

# Update PATH environment variable + set Python buffer to make Docker print every message instantly.
ENV PATH=/root/.local:$PATH \
    PYTHONUNBUFFERED=1\
    PYTHONIOENCODING=utf-8\
    PYTHONLEGACYWINDOWSSTDIO=utf-8

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY trcc_posting.py /app

#Run Python
ENTRYPOINT ["python", "-u","/app/trcc_posting.py"]