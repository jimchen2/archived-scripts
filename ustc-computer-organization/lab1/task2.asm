fibonacci_big:

    beqz a0, return_0       # 如果 n = 0，返回 0
    li t0, 1
    beq a0, t0, return_1    # 如果 n = 1，返回 1

    # 初始化64位数的变量
    li t0, 0                # F(0) 的低 32 位
    li t1, 0                # F(0) 的高 32 位
    li t2, 1                # F(1) 的低 32 位
    li t3, 0                # F(1) 的高 32 位
    
    addi a0, a0, -2         # n = n - 2，因为已处理前两种情况

loop:
    bltz a0, end_loop       # 如果 a0 < 0，退出循环
    
    # 64位加法：F(n) = F(n-1) + F(n-2)
    # 添加低 32 位
    add t4, t0, t2          # t4 = t0 + t2 (低位)
    # 添加高 32 位并处理进位
    sltu t6, t4, t2         # t5 = 进位 (如果 t4 < t2 则为 1，否则为 0)
    add t5, t1, t3          # t5 = t1 + t3 + 进位
    add t5, t5, t6          # 将进位加到高位
    
    # 为下一次迭代移动值
    mv t0, t2               # F(n-2) = F(n-1) 低位
    mv t1, t3               # F(n-2) = F(n-1) 高位
    mv t2, t4               # F(n-1) = 结果低位
    mv t3, t5               # F(n-1) = 结果高位
    
    addi a0, a0, -1         # n = n - 1
    j loop                  # 继续循环

end_loop:
    mv a0, t2               # 将低 32 位存入 a0
    mv a1, t3               # 将高 32 位存入 a1
    ret                     # 返回

return_0:
    li a0, 0                # 低 32 位 = 0
    li a1, 0                # 高 32 位 = 0
    ret                     # 返回

return_1:
    li a0, 1                # 低 32 位 = 1
    li a1, 0                # 高 32 位 = 0
    ret                     # 返回