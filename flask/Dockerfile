FROM python

COPY . .

RUN pip install flask
RUN pip install flask-sqlalchemy

EXPOSE 5000

CMD ["python","-m","flask","run","--host=0.0.0.0"]