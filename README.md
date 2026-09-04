# Codificador de instrucciones RV32I

Este proyecto consiste en un codificador de instrucciones RV32I, contando con una función que convierte la instrucción en ensamblador a su valor hexadecimal. Además se tiene una función que explica la codificación de cada instrucción.

Para validar la solución se tiene un script que compara la solución propuesta con el resultado de **RISC-V GNU Toolchain** usando `objdump`.

## Requerimientos

### Python

Se requiere Python 3, únicamente con la biblioteca estándar de este.

### RISC-V GNU Toolchain

Las pruebas se realizan  con el ensamblador RISC-V GNU y `objdump`. Se utiliza la versión de 64 bits:

```text
riscv64-unknown-elf-as
riscv64-unknown-elf-objdump
```

Con esta se puede ensamblar código en RV32I, utilizando la siguiente opción:

```text
-march=rv32i
```

## Instrucciones Soportadas

El codificador incluye las siguientes instrucciones de RV32I:

### Tipo R

```text
add
sub
and
or
```

Ejemplo de formato:
```text
instruccion rd, rs1, rs2
```

### Tipo I

```text
addi
andi
lw
lb
```

Ejemplo de formato para operaciones de ALU:

```text
instruccion rd, rs1, immediato
```

Ejemplo de formato para operaciones de Load:

```text
instruccion rd, offset(rs1)
```

El immediato o offset debe ser un valor con signo de 12 bits:

```text
-2048 to 2047
```

### Tipo S

```text
sw
sb
```

Ejemplo de formatot:

```text
instruccion rs2, offset(rs1)
```

El offset debe ser un valor con signo de 12 bits:

```text
-2048 to 2047
```

### Tipo B

```text
beq
bne
```

Ejemplo de formatot:

```text
instruccion rs1, rs2, offset
```

En RV31I el rango de desplazamiento es el siguiente, en incrementos de 2 bits:

```text
-4096 to 4094
```

## Ejecutar pruebas contra ensamblador RISC-V GNU y ejemplos

Los siguientes archivos deben estar el mismo directorio:

```text
encoder_skeleton.py
tests.s
test_encoder.py
vectores_ejemplo.txt
```

Luego se ejecuta el archivo de pruebas:

```bash
python3 test_encoder.py
```

Este ensambla el archivo:

```text
tests.s
```

Utilizando:

```bash
riscv64-unknown-elf-as \
    -march=rv32i \
    -mabi=ilp32 \
    -o rv32i_tests.o \
    rv32i_tests.s
```

Luego se utiliza:

```bash
riscv64-unknown-elf-objdump \
    -d \
    -M numeric \
    rv32i_tests.o
```

Para obtener el `objdump` que se utiliza como referencia.

---
