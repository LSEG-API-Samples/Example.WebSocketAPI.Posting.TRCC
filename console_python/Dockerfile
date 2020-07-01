FROM python:3.7-alpine

LABEL maintainer="Wasin Waeosri <wasin.waeosri@rifinitiv.com>"
LABEL build_date="2019-07-30"

# Copy requirements.txt first 
COPY requirements.txt /
# instruction to be run during image build
RUN pip install -r requirements.txt

# then copy the application
RUN mkdir /app
COPY trcc_posting.py /app
#COPY market_price.py /app
WORKDIR /app

ENTRYPOINT ["python", "-u","/app/trcc_posting.py"]