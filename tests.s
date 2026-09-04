# ADD
  add x5, x6, x7
  add x0, x31, x1
  add x31, x0, x31

# SUB
  sub x5, x6, x7
  sub x0, x31, x1
  sub x31, x0, x31

# AND
  and x5, x6, x7
  and x0, x31, x1
  and x31, x0, x31

# OR
  or x5, x6, x7
  or x0, x31, x1
  or x31, x0, x31

# ADDI
  addi x5, x6, 10
  addi x5, x6, -10
  addi x5, x6, -2048

# ANDI
  andi x5, x6, 10
  andi x5, x6, -10
  andi x5, x6, 2047

# LW
  lw x5, 12(x6)
  lw x5, -12(x6)
  lw x31, 2047(x0)

# LB
  lb x5, 12(x6)
  lb x5, -12(x6)
  lb x31, -2048(x0)

# SW
  sw x5, 12(x6)
  sw x5, -12(x6)
  sw x31, 2047(x0)

# SB
  sb x5, 12(x6)
  sb x5, -12(x6)
  sb x31, -2048(x0)

# BEQ
  beq x5, x6, .+16
  beq x5, x6, .-16
  beq x31, x0, .+4094

# BNE
  bne x5, x6, .+16
  bne x5, x6, .-16
  bne x31, x0, .-4096