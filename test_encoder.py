
import encoder_skeleton as es

EXAMPLE_FILE = "vectores_ejemplo.txt"

def main():
    print("Pruebas con ejemplos dados")
    print("=" * 78)
    print(f"Fuente    : {EXAMPLE_FILE}")
    print()

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
        f"{'Instruccion':<23} "
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

if __name__ == "__main__":
    main()