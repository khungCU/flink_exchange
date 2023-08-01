INSERT INTO orders
VALUES (10, '2020-07-30 15:22:00', 'Jark', 29.71, 104, false);

INSERT INTO shipments
VALUES (20,10004,'Shanghai','Beijing',false);

UPDATE orders SET order_status = true WHERE order_id = 10004;
UPDATE shipments SET is_arrived = true WHERE shipment_id = 1004;
DELETE FROM orders WHERE order_id = 10004;
