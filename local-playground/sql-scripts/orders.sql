CREATE TABLE public.orders (
  order_id INTEGER PRIMARY KEY,
  order_date DATE NOT NULL,
  customer_name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 5) NOT NULL,
  product_id INTEGER NOT NULL,
  order_status BOOLEAN NOT NULL -- Whether order has been placed
);
ALTER TABLE public.orders REPLICA IDENTITY FULL;


INSERT INTO orders
VALUES (1, '2020-07-30 10:08:22', 'Jark', 50.50, 102, false),
       (2, '2020-07-30 10:11:09', 'Sally', 15.00, 105, false),
       (3, '2020-07-30 12:00:30', 'Edward', 25.25, 106, false);
