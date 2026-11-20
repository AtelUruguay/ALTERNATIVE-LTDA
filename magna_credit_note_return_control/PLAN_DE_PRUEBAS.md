# Plan de pruebas manual — Control de NC por devolución

Módulo: `magna_credit_note_return_control` · Odoo 17 Enterprise

Pruebas por interfaz, para ejecutar y firmar. Cada caso indica los pasos, el resultado
esperado y el mensaje textual que debe mostrar el sistema.

---

## 1. Antes de empezar: en qué ambiente corre cada bloque

Los casos están separados en dos bloques por una razón concreta, **no por comodidad**.

El módulo `magna_factura_electronica` envía un CFE al webservice de DGI cada vez que se
**publica** una factura o una nota de crédito de cliente. En el build de QA el parámetro
`magna_fe_activa` está en `True`, así que toda NC que se publique ahí genera un CFE real
en el ambiente de test de Proinfo.

| Bloque | Casos | Dónde correrlo | Por qué |
|---|---|---|---|
| **A — No publican** | CP-01 a CP-08, CP-12 | Build de QA (staging) | El control corta antes de contabilizar; no se envía ningún CFE |
| **B — Publican** | CP-09 a CP-11, CP-13, CP-14 | Build de **development** (base vacía) | Al publicar se emite CFE. En una base vacía `magna_fe_activa` arranca en `False` y no se envía nada |

`magna_fe_activa` viene en `False` desde el propio módulo
(`magna_factura_electronica/data/fe_data.xml`). En QA está en `True` porque la base es
un clon de producción donde alguien lo activó.

> **Si vas a correr el bloque B en QA igual**, avisá antes al responsable de FE y asumí
> que se van a emitir CFE de test con datos ficticios.

**Ambiente de QA:** https://magna-qa-37121411.dev.odoo.com

---

## 2. Preparación del escenario

Hacer una sola vez por ambiente. En QA **ya está hecho**: los registros existen con el
prefijo `[TEST-CLAUDE]` y se pueden reutilizar.

### 2.1 Permisos del usuario que prueba

Ajustes → Usuarios y compañías → Usuarios → tu usuario:

- Contabilidad: **Facturación** (o superior)
- Inventario: **Usuario**
- Dejar **sin tildar** «Excepción al control de notas de crédito por devolución».
  Se activa recién en CP-11.

### 2.2 Datos

| # | Qué | Cómo |
|---|---|---|
| P1 | Cliente A | Contactos → Nuevo → nombre `[PRUEBA] Cliente Devolución`, marcar como cliente |
| P2 | Cliente B | Ídem, nombre `[PRUEBA] Cliente Otro` |
| P3 | Producto | Inventario → Productos → Nuevo → `[PRUEBA] Producto`, tipo **Producto almacenable** |
| P4 | Remito válido | Ver 2.3, con Cliente A. Debe quedar en **Hecho** |
| P5 | Remito de otro cliente | Ver 2.3, con Cliente B. Debe quedar en **Hecho** |
| P6 | Remito sin validar | Ver 2.3, con Cliente A, **sin** pulsar Validar |
| P7 | Orden de entrega | Inventario → Órdenes de entrega → Nuevo, Cliente A, sin validar |

### 2.3 Cómo crear un remito de devolución

1. Inventario → Transferencias → **Recepciones** → Nuevo.
2. Contacto: el cliente que corresponda.
3. Operación: **Recepciones** del almacén que uses.
4. En Operaciones, agregar el producto, cantidad **1**.
5. Guardar → **Marcar como pendiente** → **Validar**.
6. Confirmar que el estado quede en **Hecho**.

---

## Bloque A — Casos que no publican

### CP-01 · El motivo es obligatorio

1. Contabilidad → Clientes → **Notas de crédito** → Nuevo.
2. Cliente A. Agregar una línea con el producto, cantidad 1.
3. Dejar **Motivo de la nota de crédito** vacío. Guardar.
4. Pulsar **Confirmar**.

**Esperado:** no se confirma. Mensaje:

> Falta el motivo en la nota de crédito «…». Debe indicarlo antes de confirmarla.

---

### CP-02 · El campo Motivo solo aparece en notas de crédito de cliente

1. Abrir una **factura de cliente** cualquiera en borrador.
2. Buscar el campo «Motivo de la nota de crédito» en la cabecera.

**Esperado:** el campo no está visible. Repetir en un asiento contable: tampoco aparece.

---

### CP-03 · Devolución sin remito queda bloqueada

1. NC nueva para Cliente A, con línea.
2. Motivo: **Devolución de mercadería**. Dejar el remito vacío. Guardar.
3. **Confirmar**.

**Esperado:** no se confirma. Mensaje:

> La nota de crédito «…» se emite por devolución de mercadería, pero la mercadería
> devuelta no puede trazarse a un remito válido:
> - No se indicó ningún remito de devolución.

---

### CP-04 · Remito sin validar queda bloqueado

1. NC nueva para Cliente A, motivo **Devolución de mercadería**.
2. En **Remito de devolución**, escribir el nombre del remito P6 (sin validar).
   Si el desplegable no lo ofrece, es el comportamiento de CP-07: usar la búsqueda
   completa para forzarlo.
3. Guardar y **Confirmar**.

**Esperado:** no se confirma. Mensaje indicando que el remito no está en estado Hecho y
cuál es su estado actual.

---

### CP-05 · Remito de otro cliente rechazado al guardar

1. NC nueva para Cliente A, motivo **Devolución de mercadería**.
2. En Remito de devolución, forzar la selección del remito P5 (de Cliente B).
3. **Guardar**.

**Esperado:** no deja guardar. Mensaje:

> El remito de devolución «…» no corresponde a [PRUEBA] Cliente Devolución.

Este control salta al guardar, no al confirmar.

---

### CP-06 · Una orden de entrega no puede respaldar una NC

1. NC nueva para Cliente A, motivo **Devolución de mercadería**.
2. Forzar la selección de la orden de entrega P7.
3. **Guardar**.

**Esperado:** no deja guardar. Mensaje:

> La transferencia «…» no es una recepción y no puede respaldar una nota de crédito.

---

### CP-07 · El desplegable solo ofrece remitos válidos

1. NC nueva para Cliente A, motivo **Devolución de mercadería**.
2. Abrir el desplegable de **Remito de devolución** sin escribir nada.

**Esperado:** aparece el remito P4. **No** aparecen: el remito de Cliente B (P5), el
remito sin validar (P6), ni la orden de entrega (P7).

---

### CP-08 · Cambiar el motivo limpia el remito

1. NC nueva para Cliente A, motivo **Devolución de mercadería**, remito P4. Guardar.
2. Cambiar el motivo a **Error de facturación**.

**Esperado:** el campo Remito de devolución desaparece de la vista y queda vacío. Al
volver a poner **Devolución de mercadería**, el campo reaparece **sin** el remito
anterior.

---

### CP-12 · El campo de excepción está oculto para quien no tiene el permiso

1. Con el usuario **sin** el permiso de excepción, abrir cualquier NC con motivo
   **Devolución de mercadería**.

**Esperado:** el campo «Excepción al control de devolución» no aparece en ningún lado.
No está deshabilitado ni vacío: no existe para ese usuario.

---

## Bloque B — Casos que publican (build de development)

> Antes de arrancar: Ajustes → Técnico → Parámetros del sistema → verificar que
> `magna_fe_activa` esté en **False**. Si no existe el parámetro, mejor todavía.

### CP-09 · Camino feliz

1. NC nueva para Cliente A, con línea.
2. Motivo **Devolución de mercadería**, remito **P4**. Guardar.
3. **Confirmar**.

**Esperado:** la NC pasa a **Publicado** sin ningún mensaje de error.

---

### CP-10 · Un remito no puede respaldar dos NC publicadas

1. Con CP-09 ya ejecutado (el remito P4 quedó usado por una NC publicada).
2. Crear una **segunda** NC para Cliente A, motivo **Devolución de mercadería**.
3. Seleccionar el **mismo** remito P4.

**Esperado A:** el desplegable ya **no** ofrece P4. Forzar la selección por búsqueda.

**Esperado B:** al confirmar, no se publica. Mensaje:

> El remito de devolución «…» ya respalda la/s nota/s de crédito confirmada/s «…».

---

### CP-11 · Excepción del supervisor

1. Ajustes → Usuarios → tu usuario → tildar **Excepción al control de notas de crédito
   por devolución**. Recargar el navegador.
2. NC nueva para Cliente A, motivo **Devolución de mercadería**, **sin** remito.
3. Verificar que ahora sí aparece el campo **Excepción al control de devolución**.
4. **Sin completarlo**, pulsar Confirmar.

**Esperado A:** sigue bloqueando, con el mismo mensaje de CP-03 más una línea que indica
que puede completar la excepción para publicarla igual.

5. Completar la excepción con un texto, por ejemplo: «Mercadería en tránsito, acordado
   con el cliente. Autoriza: <nombre>». Guardar y **Confirmar**.

**Esperado B:** la NC se publica. En el **chatter** aparece un mensaje nuevo con:
- quién omitió el control,
- la lista de condiciones que no se cumplían,
- la justificación ingresada.

6. **Quitar el permiso al terminar.**

---

### CP-13 · Smart button en el remito

1. Inventario → Transferencias → abrir el remito **P4**.
2. Mirar la botonera superior.

**Esperado:** hay un botón **Notas de crédito** con el contador en 1. Al pulsarlo se
abre la NC de CP-09.

---

### CP-14 · Propagación desde el asistente de reversión

1. Preparar: una factura de cliente **publicada** para Cliente A, y un remito de
   devolución validado nuevo (repetir 2.3).
2. Abrir la factura → **Nota de crédito**.
3. En el asistente, completar **Motivo de la nota de crédito** = Devolución de
   mercadería y seleccionar el remito.
4. Pulsar **Revertir**.

**Esperado A:** la NC creada trae ya cargados el motivo y el remito.

**Esperado B:** al confirmarla, se publica sin errores.

---

## 3. Planilla de resultados

| Caso | Bloque | Resultado | Fecha | Quién | Observaciones |
|---|---|---|---|---|---|
| CP-01 | A | | | | |
| CP-02 | A | | | | |
| CP-03 | A | | | | |
| CP-04 | A | | | | |
| CP-05 | A | | | | |
| CP-06 | A | | | | |
| CP-07 | A | | | | |
| CP-08 | A | | | | |
| CP-12 | A | | | | |
| CP-09 | B | | | | |
| CP-10 | B | | | | |
| CP-11 | B | | | | |
| CP-13 | B | | | | |
| CP-14 | B | | | | |

Resultado: **OK** / **Falla** / **No aplica**. Ante una falla, anotar el mensaje textual
que mostró el sistema y el número de la NC.

---

## 4. Limpieza

- Las NC en **borrador** se pueden eliminar.
- Las NC **publicadas** no se eliminan: hay que cancelarlas y quedan en la base.
- Los remitos en estado **Hecho** no se pueden eliminar en Odoo. Los de prueba quedan.
  Por eso conviene correr el bloque B en un build de development descartable.
- Verificar que el permiso de excepción quedó **quitado** del usuario de prueba.

---

## 5. Qué no cubre este plan

- Los tests automatizados de `tests/`, que necesitan
  `odoo-bin --test-enable` desde el shell del build.
- El comportamiento en multi-compañía: hay una sola compañía.
- Notas de crédito emitidas desde Punto de Venta, fuera del alcance del módulo.
