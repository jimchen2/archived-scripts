.text
fibonacci:
    # 如果 n = 0，返回 0
    beqz a0, return_0       # 如果 a0 == 0，跳转到 return_0
    
    # 如果 n = 1，返回 1
    li t0, 1                # t0 = 1
    beq a0, t0, return_1    # 如果 a0 == 1，跳转到 return_1
    
    # 初始化变量
    li t0, 0                # t1 = F(0) = 0
    li t1, 1                # t2 = F(1) = 1
    addi a0, a0, -2         # n = n - 2，因为已经处理了前两种情况

loop:
    bltz a0, end_loop       # 如果 a0 < 0，跳转到 end_loop (修复的部分)
    add t2, t0, t1        
    mv t0, t1    
    mv t1, t2
    addi a0, a0, -1
    j loop                  # 继续循环

end_loop:
    mv a0, t2               # 将结果存入 a0
    ret                     # 返回

return_0:
    li a0, 0                # a0 = 0
    ret                     # 返回

return_1:
    li a0, 1                # a0 = 1
    ret                     # 返回