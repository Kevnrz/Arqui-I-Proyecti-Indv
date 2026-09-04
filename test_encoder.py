#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path

import encoder_skeleton as es


SCRIPT_DIR = Path(__file__).resolve().parent
EXAMPLE_FILE = SCRIPT_DIR / "vectores_ejemplo.txt"
ASM_FILE = SCRIPT_DIR / "tests.s"
OBJ_FILE = SCRIPT_DIR / "tests.o"

AS = shutil.which("riscv64-unknown-elf-as")
OBJDUMP = shutil.which("riscv64-unknown-elf-objdump")

if AS is None:
    print("ERROR: riscv64-unknown-elf-as was not found in PATH.")
    print("Install the RISC-V GNU toolchain and make sure its bin directory is in PATH.")
    sys.exit(1)

if OBJDUMP is None:
    print("ERROR: riscv64-unknown-elf-objdump was not found in PATH.")
    print("Install the RISC-V GNU toolchain and make sure its bin directory is in PATH.")
    sys.exit(1)


# These must match the instructions in rv32i_tests.s, in exactly the same order.
TESTS = [
    # ADD
    "add x5, x6, x7",
    "add x0, x31, x1",
    "add x31, x0, x31",

    # SUB
    "sub x5, x6, x7",
    "sub x0, x31, x1",
    "sub x31, x0, x31",

    # AND
    "and x5, x6, x7",
    "and x0, x31, x1",
    "and x31, x0, x31",

    # OR
    "or x5, x6, x7",
    "or x0, x31, x1",
    "or x31, x0, x31",

    # ADDI
    "addi x5, x6, 10",
    "addi x5, x6, -10",
    "addi x5, x6, -2048",

    # ANDI
    "andi x5, x6, 10",
    "andi x5, x6, -10",
    "andi x5, x6, 2047",

    # LW
    "lw x5, 12(x6)",
    "lw x5, -12(x6)",
    "lw x31, 2047(x0)",

    # LB
    "lb x5, 12(x6)",
    "lb x5, -12(x6)",
    "lb x31, -2048(x0)",

    # SW
    "sw x5, 12(x6)",
    "sw x5, -12(x6)",
    "sw x31, 2047(x0)",

    # SB
    "sb x5, 12(x6)",
    "sb x5, -12(x6)",
    "sb x31, -2048(x0)",

    # BEQ
    "beq x5, x6, 16",
    "beq x5, x6, -16",
    "beq x31, x0, 4094",

    # BNE
    "bne x5, x6, 16",
    "bne x5, x6, -16",
    "bne x31, x0, -4096",
]

def check_examples():
    examples = []
    examples_res = []

    with open(EXAMPLE_FILE) as file:
        lines = file.readlines()
        for line in lines:
            line = line.split("#")[0].strip()

            if line:
                inst, res = line.split(';')

                examples.append(inst)
                examples_res.append(res.replace(" ", ""))

    print(
        f"{'Instruccion':<18} "
        f"{'Esperado':>10}  {'Obtenido':>10}  Resultado"
    )
    print("-" * 78)

    passed = 0
    
    for i in range (0, len(examples)):
        inst = examples[i]
        word = es.encode_instruction(inst) & 0xFFFFFFFF
        res = f"0x{word:08x}"
        expected = examples_res[i]
        status = "FALLIDO"
        if res.lower() == expected:
            status = "EXITO"
            passed += 1
        print(f"{inst:25} {expected} {res} {status}")

    print("-" * 78)
    print(f"Exitos: {passed}/{len(examples)}")
    print(f"Fallos: {len(examples) - passed}/{len(examples)}")


def assemble():
    """Assemble the test source into an object file."""
    command = [
        AS,
        "-march=rv32i",
        "-mabi=ilp32",
        "-o",
        str(OBJ_FILE),
        str(ASM_FILE),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("ERROR: assembler failed.")
        print(result.stderr)
        sys.exit(1)


def get_objdump():
    """Run objdump and return its disassembly as text."""
    command = [
        OBJDUMP,
        "-d",
        "-M",
        "numeric",
        str(OBJ_FILE),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("ERROR: objdump failed.")
        print(result.stderr)
        sys.exit(1)

    return result.stdout


def parse_objdump(text):
    """
    Extract machine-code words from objdump.

    Typical objdump line:

        0:  007302b3    add x5,x6,x7

    Returns a list of integer machine-code values.
    """

    values = []

    # Address, machine word, disassembly.
    pattern = re.compile(
        r"^\s*[0-9a-fA-F]+:\s+"
        r"([0-9a-fA-F]{8})\s+"
        r".*$"
    )

    for line in text.splitlines():
        match = pattern.match(line)

        if match:
            values.append(int(match.group(1), 16))

    return values


def normalize_instruction(instruction):
    """Normalize whitespace/case for display/comparison."""
    instruction = instruction.split("#")[0]
    instruction = instruction.replace(",", ", ")
    instruction = re.sub(r"\s+", " ", instruction.strip())
    return instruction.lower()


def main():
    print("Pruebas con ejemplos dados")
    print("=" * 78)
    print(f"Fuente    : {EXAMPLE_FILE}")
    print()

    check_examples()
    print()

    print("Verificacion con Toolchain")
    print("=" * 78)
    print(f"Assembler : {AS}")
    print(f"Objdump   : {OBJDUMP}")
    print(f"Fuente    : {ASM_FILE}")
    print()

    assemble()

    objdump = get_objdump()
    reference = parse_objdump(objdump)

    if len(reference) != len(TESTS):
        print(
            f"ERROR: esperadas {len(TESTS)} instruccions del objdump, "
            f"se encontraron {len(reference)}."
        )
        print()
        print("Raw objdump:")
        print(objdump)
        sys.exit(1)

    passed = 0
    failed = 0

    print(
        f"{'#':>2}  {'Instruccion':<18} "
        f"{'GNU':>11}  {'Obtenido':>10}  Resultado"
    )
    print("-" * 78)

    for index, (instruction, reference_value) in enumerate(
        zip(TESTS, reference), start=1
    ):
        try:
            python_value = es.encode_instruction(instruction)
        except Exception as exc:
            print(
                f"{index:>2}  {instruction:<25} "
                f"{reference_value:08X}  {'ERROR':>10}  FALLIDO"
            )
            print(f"    Error del encoder: {exc}")
            failed += 1
            continue

        if python_value == reference_value:
            result = "EXITO"
            passed += 1
        else:
            result = "FALLIDO"
            failed += 1

        print(
            f"{index:>2}  {instruction:<25} "
            f"{reference_value:08X}  {python_value:08X}  {result}"
        )

    print("-" * 78)
    print(f"Exitos: {passed}/{len(TESTS)}")
    print(f"Fallos: {failed}/{len(TESTS)}")

    if failed:
        print()
        print("Se obtuvieron codificaciones erroneas.")
        print(f"Verificar objdump completo en: {OBJ_FILE}")
        sys.exit(1)

    print()
    print("TODAS LAS PRUEBAS FUERON EXITOSAS.")


if __name__ == "__main__":
    main()
