CREATE TABLE public.products (
  id INTEGER NOT NULL,
  name VARCHAR(255) NOT NULL,
  description VARCHAR(512)
);
ALTER TABLE public.products REPLICA IDENTITY FULL;

INSERT INTO products
VALUES (1,'scooter','Small 2-wheel scooter'),
       (2,'car battery','12V car battery'),
       (3,'12-pack drill bits','12-pack of drill bits with sizes ranging from #40 to #3'),
       (4,'hammer','12oz carpenter hammer'),
       (5,'hammer','14oz carpenter hammer'),
       (6,'hammer','16oz carpenter hammer'),
       (7,'rocks','box of assorted rocks'),
       (8,'jacket','water resistent black wind breaker'),
       (9,'spare tire','24 inch spare tire');