使用 RISC-V

## 任务 1：斐波那契数列（6 分）

请编写汇编程序，计算斐波那契数列的第 n 项（n≤20）。初始时，n 的值保存在 a0 中。程序执行完成后，数列的第 n 项保存在 a0 中。

F(0) = 0
F(1) = 1
F(n) = F(n-1) + F(n-2) (n≥2)

## 任务 2：大整数处理（3 分）

请编写汇编程序，计算斐波那契数列的第 n 项（n≤45）。初始时，n 的值保存在 a0 中。程序执行完成后，数列的第 n 项保存在 a0 和 a1 中，其中 a1 存储结果的高 32 位，a0 存储结果的低 32 位。

## 任务 3：导出 COE 文件（1 分）

完成汇编程序的编写之后，请导出指令段的 Coefficient File 文件，以供后续实验使用。

## COE 文件

COE 文件是 Vivado 存储器 IP 核的初始化文件。该文件可以将数据自动导入存储器中，以供其他模块单元的使用。它的一般格式如下：

```
memory_initialization_radix = 16;
memory_initialization_vector =
00008737
f0070713
000087b7
f0478793
```

其中，memory_initialization_radix 指示数据使用的进制，memory_initialization_vector 则给出了每一个存储单元保存的数据。在上面的例子里，我们有

M[0] = 00008737
M[1] = f0070713
M[2] = 000087b7
M[3] = f0478793

对于其他存储单元，初始时将被置为 0。

## Report

### Task 1

How to run the code in Rars?

**Note: I am not supposed to store function variables in the stack pointer. It is just very strange and unconventional to do so. So I stored the registers in a0.**

**Note: The first task is included in the second task.**

Just move the a0 to sp and the output to gp if you want.

1. 在 rars 里新建一个文件
2. 粘贴代码（或者编辑代码）
3. Press Run>Assemble

4. Change the Vars
5. Run>Reset
6. Run>Go

Debugging: Run>Step

If input is 1:

If input is 2:

If input is 10(a in base 16)

### Task 2

First test the input being 1, 2, 0xa in base 16 and everything works.

Set input to 20(0x14) and output 0x1a6d=6765

Set input to 30(0x1e) and output 0xcb228=832040

Set input to 50(0x32) and output 0x2 and 0xee333961=12586269025

### Task 3

Dump COE:

1. Run>Assemble
2. File>Dump memory
