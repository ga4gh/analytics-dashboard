FROM liquibase/liquibase:4.33.0

COPY dbchangelog.xml .

ENTRYPOINT ["liquibase", "--changeLogFile=dbchangelog.xml", "update"]
