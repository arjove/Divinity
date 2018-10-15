FROM python:2.7

WORKDIR /pythonapp

ADD projections.py /
ADD . .

RUN pip install -U googlemaps

VOLUME /pythonapp

EXPOSE 31337

CMD ["python2.7", "./projections.py"]
