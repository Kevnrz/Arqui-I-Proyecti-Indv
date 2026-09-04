#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import sys

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]

REGISTERS = {f"x{i}": i for i in range(32)}

def get_reg(reg):
    reg = reg.strip().lower()

    if reg not in REGISTERS:
        raise ValueError(f"Registro {reg} invalido")

    return REGISTERS[reg]

# Diccionario
# instruccion: (funct3, funct7)
R_TYPE = {
    "add": (0b000, 0b0000000),
    "sub": (0b000, 0b0100000),
    "and": (0b111, 0b0000000),
    "or":  (0b110, 0b0000000),
}

OPCODE_R = 0b0110011

def encode_r(mnemonic, operands):
    if len(operands) != 3:
        raise ValueError(f"{mnemonic} requiere rd, rs1, rs2")
    
    rd = get_reg(operands[0])
    rs1 = get_reg(operands[1])
    rs2 = get_reg(operands[2])
    
    funct3, funct7 = R_TYPE[mnemonic]
    
    instruction = (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | OPCODE_R
    )
    
    return instruction

# Diccionario
# instruccion: funct3
I_TYPE = {
    "addi": 0b000,
    "andi": 0b111,
    "lb": 0b000,
    "lw": 0b010,
}

OPCODE_I_ALU = 0b0010011
OPCODE_I_LOAD = 0b0000011

def get_imm(value):
    value = value.strip()

    if value.lower().startswith("0x"):
        return int(value, 16)

    return int(value, 10)

def check_size(value, bits):
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1

    if not minimum <= value <= maximum:
        raise ValueError(f"Tamano de inmediato {value} invalido, debe estar entre -{2**bits} y {2**bits - 1}.")

def encode_i_alu(mnemonic, operands):
    if len(operands) != 3:
        raise ValueError(f"{mnemonic} requiere rd, rs1, immediate")
    
    rd = get_reg(operands[0])
    rs1 = get_reg(operands[1])
    imm = get_imm(operands[2])

    check_size(imm, 12)
    imm12 = imm & 0xFFF # extender negativo
    
    funct3 = I_TYPE[mnemonic]
    
    instruction = (
        (imm12 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | OPCODE_I_ALU
    )
    
    return instruction

def get_memory_operands(operand):
    operand = operand.strip()

    try:
        imm_part, reg_part = operand.split("(")
        reg_part = reg_part.rstrip(")")

        imm = get_imm(imm_part)
        rs1 = get_reg(reg_part)

        return imm, rs1

    except Exception:
        raise ValueError(
            f"Error en operando de memoria: {operand}."
        )    

def encode_i_load(mnemonic, operands):
    if len(operands) != 2:
        raise ValueError(f"{mnemonic} requiere rd, offset(rs1)")

    rd = get_reg(operands[0])
    imm, rs1 = get_memory_operands(operands[1])

    check_size(imm, 12)
    imm12 = imm & 0xFFF # extender negativo

    funct3 = I_TYPE[mnemonic]

    instruction = (
        (imm12 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | OPCODE_I_LOAD
    )

    return instruction

def encode_i(mnemonic, operands):
    alu = ["addi", "andi"]
    load = ["lb", "lw"]
    if mnemonic in alu:
        return encode_i_alu(mnemonic, operands)
    elif mnemonic in load:
        return encode_i_load(mnemonic, operands)
    else:
        raise ValueError(f"Instruccion {mnemonic} no soportada")

# Diccionario
# instruccion: funct3
S_TYPE = {
    "sb": 0b000,
    "sw": 0b010,
}

OPCODE_S = 0b0100011

def get_imm_bits(value, high, low):
    width = high - low + 1
    mask = (1 << width) - 1
    return (value >> low) & mask

def encode_s(mnemonic, operands):
    if len(operands) != 2:
        raise ValueError(f"{mnemonic} requiere rs2, offset(rs1)")

    rs2 = get_reg(operands[0])
    imm, rs1 = get_memory_operands(operands[1])

    check_size(imm, 12)
    imm12 = imm & 0xFFF # extender negativo

    imm_11_5 = get_imm_bits(imm12, 11, 5)
    imm_4_0 = get_imm_bits(imm12, 4, 0)

    funct3 = S_TYPE[mnemonic]

    instruction = (
        (imm_11_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm_4_0 << 7)
        | OPCODE_S
    )

    return instruction

# Diccionario
# instruccion: funct3
B_TYPE = {
    "beq": 0b000,
    "bne": 0b001,
}

OPCODE_B = 0b1100011

def encode_b(mnemonic, operands):
    if len(operands) != 3:
        raise ValueError(f"{mnemonic} requiere rs1, rs2, offset")

    rs1 = get_reg(operands[0])
    rs2 = get_reg(operands[1])
    imm = get_imm(operands[2])

    check_size(imm, 13)

    if imm % 2 != 0:
        raise ValueError(f"Desplazamiento {imm} debe estar alineado a 2 bits")

    imm13 = imm & 0x1FFF # extender signo

    imm12 = get_imm_bits(imm13, 12, 12)
    imm10_5 = get_imm_bits(imm13, 10, 5)
    imm4_1 = get_imm_bits(imm13, 4, 1)
    imm11 = get_imm_bits(imm13, 11, 11)

    funct3 = B_TYPE[mnemonic]

    instruction = (
        (imm12 << 31)
        | (imm10_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm4_1 << 8)
        | (imm11 << 7)
        | OPCODE_B
    )

    return instruction

def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe
    retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """
    # TODO: implementar. Sugerencia: parsear el mnemónico y los operandos,
    parts = instruction.replace(",", " ").split()

    mnemonic = parts[0].lower()
    operands = parts[1:]
    # despachar según el formato (R/I/S/B), y ensamblar los campos con
    # operaciones de bits.
    if mnemonic in SOPORTADAS:
        if mnemonic in R_TYPE:
            return encode_r(mnemonic, operands)
        elif mnemonic in I_TYPE:
            return encode_i(mnemonic, operands)
        elif mnemonic in S_TYPE:
            return encode_s(mnemonic, operands)
        elif mnemonic in B_TYPE:
            return encode_b(mnemonic, operands)
    else:
        raise ValueError(f"Instruccion {mnemonic} no soportada")

def explain_r(mnemonic, operands):
    rd = get_reg(operands[0])
    rs1 = get_reg(operands[1])
    rs2 = get_reg(operands[2])

    funct3, funct7 = R_TYPE[mnemonic]

    print("Tipo         : R")
    print("Codificacion : funct7 | rs2 | rs1 | funct3 | rd | opcode")
    print()

    print(f"funct7      : {funct7:07b}")
    print(f"rs2         : {rs2:05b} = {rs2}")
    print(f"rs1         : {rs1:05b} = {rs1}")
    print(f"funct3      : {funct3:03b}")
    print(f"rd          : {rd:05b} = {rd}")
    print(f"opcode      : {OPCODE_R:07b}")

    print()
    print(
        f"Resultado  : "
        f"{funct7:07b}_{rs2:05b}_{rs1:05b}_"
        f"{funct3:03b}_{rd:05b}_{OPCODE_R:07b}"
    )

def explain_i(mnemonic, operands):
    alu = ["addi", "andi"]
    load = ["lb", "lw"]
    if mnemonic in alu:
        rd = get_reg(operands[0])
        rs1 = get_reg(operands[1])
        imm = get_imm(operands[2])
        opcode = OPCODE_I_ALU
    elif mnemonic in load:
        rd = get_reg(operands[0])
        imm, rs1 = get_memory_operands(operands[1])
        opcode = OPCODE_I_LOAD
    else:
        raise ValueError(f"Instruccion {mnemonic} no soportada")   
    
    check_size(imm, 12)

    imm12 = imm & 0xFFF
    funct3 = I_TYPE[mnemonic]

    print("Tipo         : I")
    print("Codificacion : immediato | rs1 | funct3 | rd | opcode")
    print()

    print(f"immediato   : {imm12:012b} = {imm}")
    print(f"rs1         : {rs1:05b} = {rs1}")
    print(f"funct3      : {funct3:03b}")
    print(f"rd          : {rd:05b} = {rd}")
    print(f"opcode      : {opcode:07b}")

    print()
    print(
        f"Resultado  : "
        f"{imm12:012b}_{rs1:05b}_{funct3:03b}_"
        f"{rd:05b}_{OPCODE_I_ALU:07b}"
    )

def explain_s(mnemonic, operands):
    rs2 = get_reg(operands[0])
    imm, rs1 = get_memory_operands(operands[1])

    check_size(imm, 12)

    imm12 = imm & 0xFFF

    imm_11_5 = get_imm_bits(imm12, 11, 5)
    imm_4_0 = get_imm_bits(imm12, 4, 0)

    funct3 = S_TYPE[mnemonic]

    print("Tipo         : S")
    print("Codificacion : imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode")
    print()

    print(f"imm[11:5]   : {imm_11_5:07b} = {imm_11_5}")
    print(f"rs2         : {rs2:05b} = {rs2}")
    print(f"rs1         : {rs1:05b} = {rs1}")
    print(f"funct3      : {funct3:03b}")
    print(f"imm[4:0]    : {imm_4_0:05b} = {imm_4_0}")
    print(f"opcode      : {OPCODE_S:07b}")

    print()
    print(
        f"Resultado  : "
        f"{imm_11_5:07b}_{rs2:05b}_{rs1:05b}_"
        f"{funct3:03b}_{imm_4_0:05b}_{OPCODE_S:07b}"
    )

def explain_b(mnemonic, operands):
    rs1 = get_reg(operands[0])
    rs2 = get_reg(operands[1])
    imm = get_imm(operands[2])

    check_size(imm, 13)

    if imm % 2 != 0:
        raise ValueError("Branch offset must be 2-byte aligned")

    imm13 = imm & 0x1FFF

    imm12 = get_imm_bits(imm13, 12, 12)
    imm10_5 = get_imm_bits(imm13, 10, 5)
    imm4_1 = get_imm_bits(imm13, 4, 1)
    imm11 = get_imm_bits(imm13, 11, 11)

    funct3 = B_TYPE[mnemonic]

    print("Type         : B-type")
    print("Codificacion : imm[12] | imm[10:5] | rs2 | rs1 | funct3 | imm[4:1] | imm[11] | opcode")
    print()

    print(f"imm[12]     : {imm12:01b} = {imm12}")
    print(f"imm[10:5]   : {imm10_5:06b} = {imm10_5}")
    print(f"rs2         : {rs2:05b} = {rs2}")
    print(f"rs1         : {rs1:05b} = {rs1}")
    print(f"funct3      : {funct3:03b}")
    print(f"imm[4:1]    : {imm4_1:04b} = {imm4_1}")
    print(f"imm[11]     : {imm11:01b} = {imm11}")
    print(f"opcode      : {OPCODE_B:07b}")

    print()
    print(
        f"Resultado  : "
        f"{imm12:01b}_{imm10_5:06b}_{rs2:05b}_{rs1:05b}_"
        f"{funct3:03b}_{imm4_1:04b}_{imm11:01b}_"
        f"{OPCODE_B:07b}"
    )



def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    # TODO: implementar.
    parts = instruction.replace(",", " ").split()
    mnemonic = parts[0].lower()
    operands = parts[1:]

    print("=" * 60)
    print(f"Instruccion : {instruction}")
    print()
    if mnemonic in SOPORTADAS:
        if mnemonic in R_TYPE:
            explain_r(mnemonic, operands)
        elif mnemonic in I_TYPE:
            explain_i(mnemonic, operands)
        elif mnemonic in S_TYPE:
            explain_s(mnemonic, operands)
        elif mnemonic in B_TYPE:
            explain_b(mnemonic, operands)
    else:
        raise ValueError(f"Instruccion {mnemonic} no soportada")

    print("=" * 60)


def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
