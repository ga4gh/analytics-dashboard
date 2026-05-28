FROM liquibase/liquibase:4.25.0

COPY dbchangelog.xml .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
