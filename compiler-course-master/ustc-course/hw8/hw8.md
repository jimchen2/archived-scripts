习题 6.5 6.6 6.8 6.10 6.12

## 6.5

结构体内存对齐规则导致的结果。

对于结构体 b：
```c
typedef struct _b {
    long i;  // 8字节，需要8字节对齐
    short k; // 2字节，需要2字节对齐
} b;
```
- long i：需要8字节对齐，占用0-7字节
- short k：需要2字节对齐，从第8字节开始，占用8-9字节
- 实际成员占用：10字节
- 需要填充到8的倍数：向上取整到16字节

## 6.6

```
            |              |
esp  -->    |   local var i| 
            |--------------| 
            |   old ebp    |
            |--------------| 
            | return addr  |
            |--------------| 
            |   param j+1  |
            |--------------| 
            |   local var j|
ebp  -->    |--------------| 
            |   old ebp    |
            |--------------| 
            | return addr  |
            |--------------| 
            |   param y    |
            |______________|
```
![alt text](image.png)

## 6.8


1. aa (静态全局变量)
- 存储分配：在数据段(.data)中分配8字节空间
- 作用域：仅在当前文件
- 生存期：静态生存期
- 置初值：10

2. cc (全局变量)
- 存储分配：在BSS段分配4字节空间
- 作用域：全局
- 生存期：静态生存期
- 置初值：0

3. bb (全局变量)
- 存储分配：在BSS段分配2字节空间
- 作用域：全局
- 生存期：静态生存期
- 置初值：0

4. cc.0 (static局部变量，func函数内)
- 存储分配：在BSS段分配8字节空间
- 作用域：函数作用域，仅在func函数内可见
- 生存期：静态生存期
- 置初值：0

5. dd (局部变量)
- 存储分配：在栈上分配空间
- 作用域：块作用域，仅在func函数内可见
- 生存期：动态生存期，函数调用时创建，返回时销毁
- 置初值：40

## 6.10

```c
#include <stdio.h>

int f (int x, int *py, int **ppz) { **ppz +=1; *py +=2; x +=3; return x + *py + **ppz; }

int main() {
    int c = 4;           // base value
    int *b = &c;        // b points to c
    int **a = &b;       // a points to b

    int result = f(c, b, a);
    printf("c = %d\n", c);
    printf("*b = %d\n", *b);
    printf("**a = %d\n", **a);
    printf("%d", result);
    return 0;
}
```

执行

c = 7
\*b = 7
\*\*a = 7
21

函数调用 f(c, b, a) 对应函数定义 f(int x, int \*py, int \*\*ppz)：
x 得到 c 的值，即 4
py 得到 b 的地址
ppz 得到 a 的地址

最后返回 x + \*py + \*\*ppz：

所以返回值是：7 + 7 + 7 = 21

## 6.12

- f1 使用的是 K&R C 风格的声明：`long f1( i ) long i;`
- f2 使用的是 ANSI C 风格的声明：`long f2(long i)`

1. 对于 64 位系统：

- 所有浮点参数都通过 XMM 寄存器传递

2. 对于 32 位系统：

- 浮点参数通过栈传递
- f2 的 ANSI C 声明让编译器知道参数类型是 long，会正确进行类型转换
- f1 的 K&R 声明中，编译器会默认参数为 int 类型
  - 10.0 被当作 double 存入栈
  - 为 0
