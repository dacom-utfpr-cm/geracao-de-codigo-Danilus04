; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"leiaInteiro"()

declare void @"escrevaInteiro"(i32 %".1")

define i32 @"principal"()
{
entry:
  %"a" = alloca i32, align 4
  %"b" = alloca i32, align 4
  %"c" = alloca i32, align 4
  %".2" = call i32 @"leiaInteiro"()
  store i32 %".2", i32* %"a"
  %".4" = call i32 @"leiaInteiro"()
  store i32 %".4", i32* %"b"
  %"x_temp" = load i32, i32* %"a"
  %"y_temp" = load i32, i32* %"b"
  %"soma" = add i32 %"x_temp", %"y_temp"
  store i32 %"soma", i32* %"c"
  %"x_temp.1" = load i32, i32* %"c"
  call void @"escrevaInteiro"(i32 %"x_temp.1")
  ret i32 0.0
exit:
}
