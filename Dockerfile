FROM python:3.7

WORKDIR /pythonapp

ADD projections.py /
ADD . .

RUN pip install -U googlemaps cachetools

VOLUME /pythonapp

EXPOSE 31337

CMD ["python3.7", "./projections.py"]
