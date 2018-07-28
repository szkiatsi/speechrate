FROM szkiatsi/python-janome-neologd:latest

RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY janomeutils janomeutils
COPY static static
COPY webapp.py .

EXPOSE 5000
CMD ["./webapp.py"]
