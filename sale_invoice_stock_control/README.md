# Stock Control Before Invoicing

`sale_invoice_stock_control` · Odoo 17

Impide facturar un pedido de venta cuando no hay existencias para cubrir las líneas
que lo requieren, y reserva la mercadería en ese mismo momento.

---

## 1. Qué hace

El control se dispara al **crear la factura** desde el pedido de venta — tanto con el
botón *Crear factura* como desde el asistente de facturación — y antes de que la factura
exista.

1. Toma las líneas cuyo producto es **almacenable** y tiene marcado *Requiere stock para
   facturar*. Si el pedido no tiene ninguna, no hace nada.
2. Intenta reservar los movimientos de salida pendientes de esas líneas. **Esta es la
   única reserva que ocurre**: al confirmar el pedido no se reserva nada.
3. Compara, línea por línea, lo reservado contra lo pendiente de entregar.
4. Si alguna línea no queda cubierta **por completo**, no crea la factura e informa
   producto por producto cuánto se necesita, cuánto se reservó y cuánto falta.
5. Un usuario del grupo *Puede facturar sin stock* puede facturar igual, completando una
   justificación que queda registrada en el chatter del pedido.

### Decisiones de diseño que conviene conocer

**La línea se exige entera.** Si se factura parcialmente un pedido, el control igual
exige que la línea tenga stock para toda su cantidad pendiente. No factura el remanente
disponible: bloquea y el usuario ajusta el pedido.

**Nunca devuelve una reserva ajena.** Antes de intentar reservar toma nota de lo que ya
estaba reservado. Si el control bloquea, libera únicamente lo que reservó él; lo que
depósito había reservado a mano queda intacto.

**Las facturas de anticipo quedan fuera por construcción.** El asistente de pago
anticipado construye la factura directamente y no pasa por el método que este módulo
extiende, así que no hace falta excluirlas explícitamente.

**El depósito es el del pedido.** La reserva actúa sobre los movimientos del pedido, que
salen del almacén que el pedido tiene asignado. No se evalúa contra el total de la
empresa.

---

## 2. Requisitos del entorno

| Requisito | Por qué |
|---|---|
| Tipos de operación de salida con **Método de reserva = Manualmente** | Con reserva *Al confirmar*, el stock ya queda comprometido antes de facturar y el control pierde sentido |
| Productos con **Política de facturación = Cantidades pedidas** | Con *Cantidades entregadas* no hay nada que facturar antes de entregar, y el control nunca llega a actuar |

Depende de `sale_stock`. No modifica ningún modelo, vista ni flujo estándar: todo por
herencia de `sale.order` y `product.template`.

---

## 3. Configuración

**Marca por producto** — ficha del producto → pestaña **Ventas** → grupo *Control de
stock* → **Requiere stock para facturar**. Solo visible en productos almacenables.

**Rol de excepción** — Ajustes → Usuarios y compañías → Usuarios → sección **Ventas** →
**Puede facturar sin stock**.

**Campo de justificación** — en el pedido de venta, pestaña *Otra información*, grupo
*Control de stock*. Solo existe para quien tiene el rol; el resto no lo ve.

---

## 4. Límites conocidos

- **No libera la reserva si la factura se cancela o se elimina.** Es deliberado:
  desreservar automáticamente podría sacarle mercadería a un remito que depósito está
  preparando. Si se necesita, es un agregado a definir.
- **No controla facturas creadas desde Contabilidad**, sin partir de un pedido de venta.
- **No controla la validación de la entrega**: actúa sobre la factura, no impide que
  depósito valide un remito.
- **No aplica a Punto de Venta.**

---

## 5. Prueba manual

> **Se puede correr entero en un ambiente con facturación electrónica activa.** El
> control actúa al *crear* la factura, que queda en borrador. Mientras no se confirme esa
> factura no se emite ningún CFE. **No confirmar las facturas que generen estas pruebas.**

### 5.1 Preparación

**Paso 0 — Reserva manual.** Inventario → Configuración → Tipos de operación → la
operación de entrega del almacén → **Método de reserva = Manualmente**.

**Paso 1 — Producto controlado.** Inventario → Productos → Nuevo:
- Nombre `[PRUEBA] Producto controlado`
- Tipo de producto: **Producto almacenable**
- Pestaña Ventas → Política de facturación: **Cantidades pedidas**
- Pestaña Ventas → grupo Control de stock → tildar **Requiere stock para facturar**

**Paso 2 — Producto sin control.** Igual al anterior, nombre `[PRUEBA] Producto libre`,
pero **sin** tildar la marca.

**Paso 3 — Cliente.** Contactos → Nuevo → `[PRUEBA] Cliente`.

**Paso 4 — Dejar el stock en cero.** Inventario → Operaciones → Ajustes de inventario →
buscar el producto controlado → cantidad contada **0** → Aplicar.

**Cómo fijar stock** (se usa en varios casos): mismo camino del paso 4, poniendo la
cantidad que pida el caso.

**Cómo crear el pedido** (se usa en todos los casos): Ventas → Pedidos → Nuevo → cliente
de prueba → una línea con el producto y la cantidad que pida el caso → **Confirmar**.

---

### CP-01 · Sin stock, no deja facturar

1. Stock del producto controlado en **0**.
2. Pedido con **5** unidades. Confirmar.
3. Pulsar **Crear factura** → Crear borrador de factura.

**Esperado:** no se crea la factura. Mensaje:

> No se puede facturar el pedido S00xxx: no hay stock suficiente para reservar la
> cantidad completa de estas líneas.
>
> - [PRUEBA] Producto controlado: se necesitan 5.0, se reservaron 0.0, faltan 5.0 (Unidades)
>
> Ajuste las cantidades del pedido de venta, o solicite una autorización para facturar sin stock.

---

### CP-02 · Stock parcial, bloquea igual

1. Stock en **3**.
2. Pedido con **5** unidades. Confirmar.
3. **Crear factura**.

**Esperado:** bloquea. El mensaje indica *se reservaron 3.0, faltan 2.0*. Es el caso
central del diseño: no se factura lo disponible, se bloquea la línea entera.

---

### CP-03 · Con stock completo, factura y reserva

1. Stock en **5**.
2. Pedido con **5** unidades. Confirmar.
3. **Crear factura**.

**Esperado A:** la factura se crea en borrador, sin mensajes.

**Esperado B:** abrir el remito del pedido (botón *Entrega*). Está en estado **Listo** y
los movimientos muestran las 5 unidades reservadas.

> No confirmar esta factura.

---

### CP-04 · Confirmar el pedido no reserva nada

1. Stock en **5**.
2. Pedido con **5** unidades. Confirmar.
3. **Antes de facturar**, abrir el remito.

**Esperado:** el remito **no** está reservado. Es lo que verifica que la reserva ocurre
al facturar y no antes.

---

### CP-05 · Producto sin la marca no se controla

1. Stock del producto libre en **0**.
2. Pedido con **5** unidades de `[PRUEBA] Producto libre`. Confirmar.
3. **Crear factura**.

**Esperado:** la factura se crea sin bloqueo.

---

### CP-06 · Un servicio no se controla

1. Crear un producto tipo **Servicio** con la marca tildada.
2. Pedido con ese servicio. Confirmar. **Crear factura**.

**Esperado:** la factura se crea. El control solo mira productos almacenables.

---

### CP-07 · La reserva de depósito no se toca

1. Stock en **3**.
2. Pedido con **5** unidades. Confirmar.
3. Abrir el remito → **Verificar disponibilidad**. Quedan 3 reservadas.
4. Volver al pedido → **Crear factura**.

**Esperado A:** bloquea, como en CP-02.

**Esperado B:** volver al remito. Las **3 unidades siguen reservadas**. El control no
devolvió lo que depósito había reservado.

---

### CP-08 · Autorizado sin justificación sigue bloqueado

1. Asignarse el rol **Puede facturar sin stock**. Recargar el navegador.
2. Stock en **0**. Pedido con 5 unidades. Confirmar.
3. Sin completar nada, **Crear factura**.

**Esperado:** bloquea con el mismo mensaje de CP-01. Tener el rol no alcanza.

---

### CP-09 · Autorizado con justificación factura y deja traza

1. Mismo pedido de CP-08.
2. Pestaña **Otra información** → grupo Control de stock → completar **Excepción al
   control de stock**, por ejemplo: «Entrega urgente acordada con el cliente. Autoriza:
   <nombre>». Guardar.
3. **Crear factura**.

**Esperado A:** la factura se crea.

**Esperado B:** en el **chatter del pedido** aparece un mensaje nuevo con:
- quién omitió el control,
- la lista de líneas que no se pudieron cubrir,
- la justificación ingresada.

4. **Quitarse el rol al terminar.**

---

### CP-10 · El campo de excepción no existe sin el rol

1. Con el rol **quitado**, abrir cualquier pedido → pestaña Otra información.

**Esperado:** el grupo *Control de stock* no aparece. No está vacío ni deshabilitado: no
existe para ese usuario.

---

### CP-11 · Las facturas de anticipo no se bloquean

1. Stock en **0**. Pedido con 5 unidades del producto controlado. Confirmar.
2. **Crear factura** → elegir **Anticipo (porcentaje)** → 20% → Crear borrador.

**Esperado:** la factura de anticipo se crea sin bloqueo.

---

### CP-12 · Facturar parcialmente sigue exigiendo la línea completa

1. Stock en **3**. Pedido con **5** unidades. Confirmar.
2. Bajar a **3** la cantidad a facturar (columna *Cantidad a facturar*, si el flujo lo
   permite) y **Crear factura**.

**Esperado:** bloquea igual. El control evalúa la cantidad pendiente de la línea, no la
que se está facturando.

---

### 5.2 Planilla de resultados

| Caso | Resultado | Fecha | Quién | Observaciones |
|---|---|---|---|---|
| CP-01 | | | | |
| CP-02 | | | | |
| CP-03 | | | | |
| CP-04 | | | | |
| CP-05 | | | | |
| CP-06 | | | | |
| CP-07 | | | | |
| CP-08 | | | | |
| CP-09 | | | | |
| CP-10 | | | | |
| CP-11 | | | | |
| CP-12 | | | | |

Resultado: **OK** / **Falla** / **No aplica**. Ante una falla, anotar el mensaje textual
y el número del pedido.

### 5.3 Limpieza

- Las facturas en borrador generadas se pueden eliminar.
- Los pedidos se pueden cancelar; los remitos asociados quedan cancelados.
- Verificar que el rol de excepción quedó **quitado** del usuario de prueba.
- Si se cambió el método de reserva del tipo de operación para probar, dejarlo como
  estaba.

---

## 6. Pruebas automatizadas

El módulo trae 13 tests que cubren lo mismo que el plan manual más el detalle de la
reserva. Necesitan shell del servidor:

```bash
odoo-bin -d <base> -u sale_invoice_stock_control \
  --test-enable --test-tags /sale_invoice_stock_control --stop-after-init
```

En Odoo.sh, la vía natural es pushear a una rama de **development**: el build se levanta
con base vacía, instala el módulo corriendo sus tests y deja el resultado en el log,
fechado y archivado.
