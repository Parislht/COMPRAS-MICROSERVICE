/*CANTIDAD TOTAL VENDIDA POR LIBRO*/
SELECT 
  libro_id,
  SUM(cantidad) AS total_unidades
FROM "proyecto-compras"."items-comprados-t"
GROUP BY libro_id
ORDER BY total_unidades DESC;

/*GASTO TOTAL POR USUSARIO*/
SELECT 
  username,
  SUM(total) AS gasto_total
FROM "proyecto-compras"."compras-t"
GROUP BY username
ORDER BY gasto_total DESC;

/* Libros más comprados por un usuario específico*/
SELECT 
  i.libro_id,
  SUM(i.cantidad) AS cantidad_total
FROM "proyecto-compras"."items-comprados-t" i
JOIN "proyecto-compras"."compras-t" c
  ON i.compra_id = c.compra_id
WHERE c.username = 'USUARIO1' /*CAMBIAR USUARIO DESEADO
GROUP BY i.libro_id
ORDER BY cantidad_total DESC;
