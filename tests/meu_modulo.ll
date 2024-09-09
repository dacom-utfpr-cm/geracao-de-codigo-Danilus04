; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"leiaInteiro"()

declare float @"leiaFlutuante"()

declare void @"escrevaInteiro"(float %".1")

declare void @"escrevaFlutuante"(float %".1")

define i32 @"principal"()
{
entry:
  %"x" = alloca i32, align 4
  %"y" = alloca float, align 4
  store i32 0.0, i32* %"x"
  store float              0x0, float* %"y"
  %".4" = call i32 @"leiaInteiro"()
  store i32 %".4", i32* %"x"
  %".6" = call float @"leiaFlutuante"()
  store float %".6", float* %"y"
  ret i32 0.0
exit:
}
