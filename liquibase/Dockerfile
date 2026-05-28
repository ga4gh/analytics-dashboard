FROM --platform=linux/amd64 liquibase/liquibase:4.25.0

COPY dbchangelog.xml .

CMD ["liquibase", "--changeLogFile=dbchangelog.xml", "update"]
