FROM python:3.6-alpine

RUN mkdir /app
WORKDIR /app
COPY requirements.txt .

RUN apk add --no-cache curl && \
    pip install -r requirements.txt
RUN FILE_ID=14CK0rkep2nvVpfGCJu_QQFf2PUkcI6BN && \
    FILE_NAME=/tmp/Janome.tar.gz && \
    COOKIE=/tmp/cookie && \
    curl -sc $COOKIE "https://drive.google.com/uc?export=download&id=${FILE_ID}" > /dev/null && \
    CODE="$(awk '/_warning_/ {print $NF}' /tmp/cookie)" && \
    curl -Lb $COOKIE "https://drive.google.com/uc?export=download&confirm=${CODE}&id=${FILE_ID}" -o ${FILE_NAME}  && \
    pip install ${FILE_NAME} --no-compile && \
    python -c "from janome.tokenizer import Tokenizer; Tokenizer(mmap=True)" && \
    rm ${FILE_NAME}

COPY janomeutils janomeutils
COPY static static
COPY webapp.py .

EXPOSE 5000
CMD ["./webapp.py"]
