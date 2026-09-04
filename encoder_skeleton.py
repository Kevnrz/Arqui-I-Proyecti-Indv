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
        raise ValueError(f"Invalid register: {reg}")

    return REGISTERS[reg]

# Diccionario
# instruccion: (funct3, funct7)
R_TYPE = {
    "add": (0b000, 0b0000000),
    "sub": (0b000, 0b0100000),
    "and": (0b111, 0b0000000),
    "or":  (0b110, 0b0000000),
}

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
        | 0b0110011
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

def get_imm(value):
    value = value.strip()

    if value.lower().startswith("0x"):
        return int(value, 16)

    return int(value, 10)

def check_size(value, bits):
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1

    if not minimum <= value <= maximum:
        raise ValueError(
            f"Immediato {value} es muy grande, no cabe en {bits} bits con signo"
        )

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
        | 0b0010011
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
        | 0b0000011
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
        raise ValueError(
            f"Instruccion {mnemonic} no soportada"
        )

# Diccionario
# instruccion: funct3
S_TYPE = {
    "sb": 0b000,
    "sw": 0b010,
}

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
        | 0b0100011
    )

    return instruction

# Diccionario
# instruccion: funct3
B_TYPE = {
    "beq": 0b000,
    "bne": 0b001,
}

def encode_b(mnemonic, operands):
    if len(operands) != 3:
        raise ValueError(f"{mnemonic} requiere rs1, rs2, offset")

    rs1 = get_reg(operands[0])
    rs2 = get_reg(operands[1])
    imm = get_imm(operands[2])

    check_size(imm, 13)

    if imm % 2 != 0:
        raise ValueError(
            f"Desplazamiento {imm} debe estar alineado a 2 bits"
        )

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
        | 0b1100011
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
        raise ValueError(
            f"Instruccion {mnemonic} no soportada"
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
    raise NotImplementedError("explain_instruction: pendiente de implementar")


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
